import sys
import docker
import os
import redis
import time
import json
import datetime

from core.languages.python.helpers.job_config_helpers import read_job_config
from core.languages.python.helpers.docker_helpers import (
    build_image_run_container,
    module_path_to_image_tag,
)
from core.languages.python.helpers.DockexRedisClient import DockexRedisClient
from core.experiment.helpers.ftp_find_file import ftp_find_file
from core.languages.python.helpers.path_helpers import check_make_directory
from core.experiment.helpers.get_module_stats_keys import get_module_stats_keys
from core.languages.python.helpers.job_config_helpers import write_job_config


class DockerWrapper:
    def __init__(self, input_args):
        super().__init__()

        self.json_pathname = input_args[1]
        self.redis_address = input_args[2]
        self.redis_client = DockexRedisClient(self.redis_address)

        self.tmp_dockex_path = self.redis_client.get("tmp_dockex_path")

        self.docker_client = docker.from_env()

        self.job_config = read_job_config(self.json_pathname)

        self.dockerfile_path = f"{self.job_config['path']}/Dockerfile"

        if "image_tag" in self.job_config.keys():
            self.image_tag = self.job_config["image_tag"]
        else:
            self.image_tag = module_path_to_image_tag(self.job_config["path"])

        self.command_args = self.generate_command_args()
        self.volumes = self.generate_volumes()
        self.network_mode = "host"

        self.environment = None
        if "include_json_pathname_env_variable" in self.job_config.keys():
            if self.job_config["include_json_pathname_env_variable"]:
                self.environment = {"JSON_PATHNAME": self.json_pathname}

        self.skip_build = False
        if "skip_docker_wrapper_build" in self.job_config.keys():
            if self.job_config["skip_docker_wrapper_build"] is True:
                self.skip_build = True

        # build path depends on if path is in core or relative to /tmp/dockex/project
        if self.job_config["path"].startswith("core/"):
            self.build_path = "."
        else:
            self.build_path = "/tmp/dockex/project"

        if "experiment_job" in self.job_config.keys():
            self.experiment_job = self.job_config["experiment_job"]
        else:
            self.experiment_job = False

        if self.experiment_job is True:
            self.detach = False
        else:
            self.detach = True

        self.build_kwargs_dict = dict(
            path=self.build_path, dockerfile=self.dockerfile_path, tag=self.image_tag
        )

        self.run_kwargs_dict = dict(
            image=self.image_tag,
            name=self.job_config["name"],
            command=self.command_args,
            detach=self.detach,
            network_mode=self.network_mode,
            volumes=self.volumes,
            environment=self.environment,
        )

        # check global gpus enable
        if self.redis_client.get("enable_gpus") is True:
            self.run_kwargs_dict["enable_gpus"] = True
        else:
            self.run_kwargs_dict["enable_gpus"] = False

        # allow module to override global gpus enable
        if "enable_gpus" in self.job_config.keys():
            if self.job_config["enable_gpus"] is True:
                self.run_kwargs_dict["enable_gpus"] = True
            else:
                self.run_kwargs_dict["enable_gpus"] = False

        self.good_to_launch = None
        self.experiment_manager_address = None
        self.experiment_manager = None
        self.dependency_lookup_db = None
        self.job_lookup_db = None
        self.stats_keys = None
        self.container_data_prefix = "/tmp/dockex/data/"

        self.sleep_seconds = 0.25

    def generate_command_args(self):
        command_args = f"{self.json_pathname}"

        if "omit_json_pathname_arg" in self.job_config.keys():
            if self.job_config["omit_json_pathname_arg"]:
                command_args = ""

        if "pass_redis_address_arg" in self.job_config.keys():
            if self.job_config["pass_redis_address_arg"]:
                if command_args == "":
                    command_args = f"{self.redis_address}"
                else:
                    command_args = f"{command_args} {self.redis_address}"

        if "command_args" in self.job_config.keys():
            if command_args == "":
                command_args = f"{self.job_config['command_args']}"
            else:
                command_args = f"{command_args} {self.job_config['command_args']}"

        return command_args

    def generate_volumes(self):
        volumes = {self.tmp_dockex_path: {"bind": "/tmp/dockex", "mode": "rw"}}

        if "bind_mount_docker_socket" in self.job_config.keys():
            if self.job_config["bind_mount_docker_socket"]:
                volumes["/var/run/docker.sock"] = {
                    "bind": "/var/run/docker.sock",
                    "mode": "rw",
                }

        if "volumes" in self.job_config.keys():
            for volume_key in self.job_config["volumes"].keys():
                volumes[volume_key] = {
                    "bind": self.job_config["volumes"][volume_key],
                    "mode": "rw",
                }

        return volumes

    def connect_to_experiment_manager(self):
        print("GETTING MANAGER REDIS ADDRESS")
        keep_trying = True
        while keep_trying:
            self.experiment_manager_address = self.redis_client.get(
                "manager_redis_address"
            )

            if self.experiment_manager_address is not None:
                keep_trying = False
                print("FOUND MANAGER REDIS ADDRESS")
            else:
                print("NO MANAGER FOUND, TRYING AGAIN")
                time.sleep(self.sleep_seconds)

        print("CONNECTING TO EXPERIMENT MANAGER")
        self.experiment_manager = DockexRedisClient(self.experiment_manager_address)

        experiment_manager_ip_address = self.experiment_manager.get("ip_address")
        experiment_manager_port = self.experiment_manager.get("redis_port")

        self.dependency_lookup_db = redis.StrictRedis(
            host=experiment_manager_ip_address, port=experiment_manager_port, db=1
        )
        self.job_lookup_db = redis.StrictRedis(
            host=experiment_manager_ip_address, port=experiment_manager_port, db=3
        )

    def prepare_input_pathnames(self):
        input_pathnames = self.job_config["input_pathnames"]

        if len(input_pathnames.keys()) > 0:
            # loop through ftp clients, connect, keep trying until it connects (in case workers take a while to spin up
            for input_pathname_key in input_pathnames.keys():
                input_pathname = input_pathnames[input_pathname_key]

                if input_pathname is not None:
                    local_input_pathname = (
                        f"{self.container_data_prefix}{input_pathname}"
                    )

                    # if the file doesn't exist, go find it
                    print("CHECKING FOR FILE: " + local_input_pathname)
                    if not os.path.isfile(local_input_pathname):
                        print("GOING TO LOOK FOR FILE")
                        ftp_find_file(
                            self.experiment_manager.get_list("dockex_machines"),
                            self.redis_client.get("ip_address"),
                            f"data/{input_pathname}",
                            local_input_pathname,
                        )

                    # update input_pathnames with local path
                    input_pathnames[input_pathname_key] = local_input_pathname

            # assign local input pathnames to job config for job
            self.job_config["input_pathnames"] = input_pathnames

        # check that all input pathnames exist
        if len(self.job_config["input_pathnames"].values()) > 0:
            check_pathnames = [
                os.path.isfile(check_pathname)
                for check_pathname in self.job_config["input_pathnames"].values()
                if check_pathname is not None
            ]
            self.good_to_launch = all(check is True for check in check_pathnames)
        else:
            self.good_to_launch = True

    def prepare_output_pathnames(self):
        output_pathnames = self.job_config["output_pathnames"]
        if len(output_pathnames.keys()) > 0:
            for output_pathname_key in output_pathnames.keys():
                output_pathname = output_pathnames[output_pathname_key]
                if output_pathname is not None:
                    local_output_pathname = (
                        f"{self.container_data_prefix}{output_pathname}"
                    )

                    # if the file is inside a directory, make sure that directory exists
                    local_output_path = os.path.split(local_output_pathname)[0]
                    if local_output_path != "":
                        check_make_directory(local_output_path)

                        os.system(f"chown -R nonroot:nonroot {local_output_path}")

                    output_pathnames[output_pathname_key] = local_output_pathname

            self.job_config["output_pathnames"] = output_pathnames

    def launch_experiment_job(self):
        print("GOOD TO LAUNCH")
        # overwrite json file with local input/output pathnames
        write_job_config(self.json_pathname, self.job_config)

        # update pending ready running numbers for experiment and job_command
        # use a backend pipeline so it's all atomic
        # this is a job going from ready to running
        update_pipeline = self.experiment_manager.strict_redis.pipeline()
        update_pipeline.decr("num_ready_jobs")
        update_pipeline.decr(self.stats_keys["num_ready_jobs"])
        update_pipeline.incr("num_running_jobs")
        update_pipeline.incr(self.stats_keys["num_running_jobs"])
        update_pipeline.execute()

        start_time = datetime.datetime.now()

        # launch the job
        try:
            build_image_run_container(
                self.docker_client,
                self.build_kwargs_dict,
                self.run_kwargs_dict,
                print_build_logs=True,
                skip_build=self.skip_build,
                native_run=True,
            )

        except Exception as e:
            print("EXCEPTION WHILE RUNNING CONTAINER")
            print(e)

        end_time = datetime.datetime.now()

        self.job_config["start_time"] = str(start_time)
        self.job_config["end_time"] = str(end_time)
        self.job_config["execution_time"] = str(end_time - start_time)

        print("GOOD LAUNCH")

    def cleanup_job(self):
        # release the credits
        self.redis_client.strict_redis.decrby(
            "cpu_credits_used", int(self.job_config["cpu_credits"])
        )
        self.redis_client.strict_redis.decrby(
            "gpu_credits_used", int(self.job_config["gpu_credits"])
        )

        skip_output_pathnames = self.job_config["skip_output_pathnames"]
        if type(skip_output_pathnames) is not list:
            if skip_output_pathnames is True:
                skip_output_pathnames = list(skip_output_pathnames.keys())
            else:
                skip_output_pathnames = []

        # check if its output_pathnames exist
        successful_job = True
        for local_output_pathname_key in self.job_config["output_pathnames"].keys():
            # local output_pathname contains the container_data_prefix
            local_output_pathname = self.job_config["output_pathnames"][
                local_output_pathname_key
            ]

            # remove the local data_path prepend
            output_pathname = local_output_pathname.replace(
                self.container_data_prefix, ""
            )

            # if the output_pathname doesn't exist and we're not skipping that output_pathname, an error occurred
            if not os.path.isfile(local_output_pathname):
                if local_output_pathname_key not in skip_output_pathnames:
                    # set the flag
                    successful_job = False

            # if the file does exist, save the output if requested
            # NOTE: it's important to push to output_saver before updating num_complete_jobs
            # NOTE: because ExperimentManager assumes this to determine when experiment has ended
            else:
                if self.job_config["save_outputs"]:
                    self.experiment_manager.rpush("output_saver", output_pathname)

            self.check_dependencies(output_pathname)

        # update the progress counts on ExperimentStager
        # this is a running to complete
        update_pipeline = self.experiment_manager.strict_redis.pipeline()
        update_pipeline.decr("num_running_jobs")
        update_pipeline.decr(self.stats_keys["num_running_jobs"])
        update_pipeline.incr("num_complete_jobs")
        update_pipeline.incr(self.stats_keys["num_complete_jobs"])
        update_pipeline.execute()

        if successful_job:
            self.job_config["status"] = "SUCCESS"

        else:
            self.job_config["status"] = "ERROR"

            # push to error_jobs list
            self.experiment_manager.rpush("error_jobs", self.job_config)

            # update progress counts
            update_pipeline = self.experiment_manager.strict_redis.pipeline()
            update_pipeline.incr("num_error_jobs")
            update_pipeline.incr(self.stats_keys["num_error_jobs"])
            update_pipeline.execute()

        job_config_json = json.dumps(self.job_config)

        # write job dict with status to backend
        self.job_lookup_db.set(self.job_config["name"], job_config_json)

    def check_dependencies(self, output_pathname):

        # get the job keys that depend on this output_pathname
        print("OUTPUT_PATHNAME: " + output_pathname)
        dependent_job_names = [
            b.decode("utf-8")
            for b in self.dependency_lookup_db.smembers(output_pathname)
        ]
        print("DEPENDENCY NAMES: " + str(dependent_job_names))

        for dependent_job_name in dependent_job_names:
            print("PROCESSING DEPENDENCY: " + dependent_job_name)
            self.experiment_manager.rpush("decrement_dependency", dependent_job_name)

    def failure_to_launch(self):
        # report error
        print("BAD LAUNCH")
        self.job_config["status"] = "ERROR"
        print(self.job_config)

        # ExperimentWorker checked out a cpu_credit before launching JobWrapperer
        # since job errored, check credit back in
        self.redis_client.strict_redis.decrby(
            "cpu_credits_used", int(self.job_config["cpu_credits"])
        )
        self.redis_client.strict_redis.decrby(
            "gpu_credits_used", int(self.job_config["gpu_credits"])
        )

        # push to error_jobs list
        self.experiment_manager.rpush("error_jobs", self.job_config)
        self.job_lookup_db.set(self.job_config["name"], json.dumps(self.job_config))

        # propagate error for dependent jobs
        for local_output_pathname in self.job_config["output_pathnames"].values():
            # remove the local data_path prepend
            output_pathname = local_output_pathname.replace(
                self.container_data_prefix, ""
            )
            self.check_dependencies(output_pathname)

        # update progress counts
        # ready to complete/error
        update_pipeline = self.experiment_manager.strict_redis.pipeline()
        update_pipeline.decr("num_ready_jobs")
        update_pipeline.decr(self.stats_keys["num_ready_jobs"])
        update_pipeline.incr("num_error_jobs")
        update_pipeline.incr(self.stats_keys["num_error_jobs"])
        update_pipeline.incr("num_complete_jobs")
        update_pipeline.incr(self.stats_keys["num_complete_jobs"])
        update_pipeline.execute()

    def run(self):
        print(self.job_config)

        print("build kwargs:")
        print(self.build_kwargs_dict)

        print("run kwargs")
        print(self.run_kwargs_dict)

        if self.experiment_job is not True:
            build_image_run_container(
                self.docker_client,
                self.build_kwargs_dict,
                self.run_kwargs_dict,
                print_build_logs=True,
                skip_build=self.skip_build,
                native_run=True,
            )

        else:
            print("RUNNING EXPERIMENT JOB")
            self.connect_to_experiment_manager()
            self.prepare_input_pathnames()
            self.prepare_output_pathnames()

            self.stats_keys = get_module_stats_keys(self.job_config["module_name"])

            if self.good_to_launch:
                self.launch_experiment_job()
                self.cleanup_job()
            else:
                self.failure_to_launch()

            # make sure there aren't any lingering root permission files
            os.system(f"chown -R nonroot:nonroot {self.container_data_prefix}")

            print("SUCCESS")


if __name__ == "__main__":
    DockerWrapper(sys.argv).run()
