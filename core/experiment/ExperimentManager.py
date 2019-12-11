import json
import os
import copy
import abc
import time
import redis
import pandas as pd
import datetime
import pathlib
from collections import OrderedDict
from distutils.dir_util import copy_tree
import docker
import shutil
import collections.abc

from core.languages.python.helpers.job_config_helpers import read_job_config
from core.languages.python.helpers.DockexRedisClient import DockexRedisClient
from core.services.experiment.output_saver.output_saver import CLOSE_ZIP_COMMAND
from core.languages.python.helpers.path_helpers import empty_make_directory
from core.languages.python.helpers.docker_helpers import build_project_modules
from core.experiment.helpers.ready_jobs_dict_to_key import ready_jobs_dict_to_key
from core.experiment.helpers.get_module_stats_keys import get_module_stats_keys
from core.experiment.helpers.print_progress import print_progress


def update(dict_to_update, dict_with_updates):
    for key, val in dict_with_updates.items():
        if isinstance(val, collections.abc.Mapping):
            dict_to_update[key] = update(dict_to_update.get(key, {}), val)
        else:
            dict_to_update[key] = val
    return dict_to_update


class ExperimentManager(abc.ABC):
    def __init__(
        self,
        project_path="/home/experiment/project",  # according to core/experiment/dockex_experiment
        tmp_dockex_path="/tmp/dockex",
        initial_job_num=None,
        experiment_name_prefix=None,
        sleep_seconds=0.5,
        save_project=False,
    ):

        super().__init__()

        if project_path is None:
            raise ValueError("A project_path must be provided.")
        else:
            self.project_path = os.path.expanduser(project_path)

        self.tmp_dockex_path = tmp_dockex_path

        self.dockex_config = read_job_config(tmp_dockex_path + "/dockex_config.json")
        self.redis_client = DockexRedisClient(self.dockex_config["redis_address"])

        self.docker_client = docker.from_env()

        manager_ip_address = self.redis_client.get("ip_address")
        manager_port = self.redis_client.get("redis_port")

        self.dependency_lookup_db = redis.StrictRedis(
            host=manager_ip_address, port=manager_port, db=1
        )
        self.dependency_counts_db = redis.StrictRedis(
            host=manager_ip_address, port=manager_port, db=2
        )
        self.job_lookup_db = redis.StrictRedis(
            host=manager_ip_address, port=manager_port, db=3
        )

        self.initial_job_num = initial_job_num
        if self.initial_job_num is not None:
            self.job_num = self.initial_job_num
        else:
            self.job_num = self.redis_client.get("manager_job_num")

        self.sleep_seconds = sleep_seconds

        self.job_list = []

        self.dockex_path_list = self.redis_client.get("dockex_path_list")

        self.experiment_name_prefix = experiment_name_prefix
        self.experiment_name = f"dockex_{str(datetime.datetime.now()).replace('-', '_').replace(' ', '_').replace(':', '_').split('.')[0]}"
        if self.experiment_name_prefix is not None:
            self.experiment_name = (
                f"{self.experiment_name_prefix}_{self.experiment_name}"
            )

        self.csv_filename = f"{self.experiment_name}.csv"
        self.csv_pathname = (
            f"/tmp/dockex/data/{self.csv_filename}"
        )  # this assumes we're running in a container or using /tmp/dockex locally

        self.extra_output_pathnames = []
        self.save_project = save_project
        self.project_archive_pathname = None
        self.project_archive_filename = None

    def send_to_output_saver(self, extra_output_pathname):
        self.extra_output_pathnames.append(extra_output_pathname)

    def generate_job_name(self, module_name):
        job_num = self.job_num
        job_name = f"{module_name}_{str(self.job_num)}"
        self.job_num += 1
        return job_name, job_num

    def add_job(
        self,
        module_path,
        params=None,
        input_pathnames=None,
        skip_job=False,
        skip_input_pathnames=False,
        skip_output_pathnames=False,
        cpu_credits=1,
        gpu_credits=0,
        save_outputs=False,
        params_nested_update=False,
    ):

        if cpu_credits == 0 and gpu_credits == 0:
            raise ValueError("Either cpu_credits or gpu_credits must be > 0")

        if params is None:
            params = dict()

        if input_pathnames is None:
            input_pathnames = dict()

        module_name = pathlib.PurePath(module_path).name
        config_pathname = f"{self.project_path}/{module_path}/{module_name}.json"

        with open(config_pathname, "r") as fp:
            config = json.load(fp)

        job_name, job_num = self.generate_job_name(module_name)

        config["name"] = job_name
        config["job_num"] = job_num
        config["path"] = module_path
        config["module_name"] = module_name

        config["params_nested_update"] = params_nested_update

        if "params" in config.keys():
            if params_nested_update:
                config["params"] = update(copy.deepcopy(config["params"]), params)
            else:
                config["params"].update(params)

        else:
            config["params"] = params

        if "input_pathnames" in config.keys():
            config["input_pathnames"].update(input_pathnames)
        else:
            config["input_pathnames"] = input_pathnames

        config["skip_job"] = skip_job
        config["skip_input_pathnames"] = skip_input_pathnames
        config["skip_output_pathnames"] = skip_output_pathnames
        config["cpu_credits"] = cpu_credits
        config["gpu_credits"] = gpu_credits
        config["save_outputs"] = save_outputs

        config[
            "skip_docker_wrapper_build"
        ] = (
            True
        )  # ExperimentWorker takes care of building containers before wrapper launched

        config["experiment_job"] = True

        for params_key in config["params"].keys():
            if config["params"][params_key] == "DOCKEX_REQUIRED":
                raise ValueError(
                    f'Missing required parameter "{params_key}" for job name "{job_name}"'
                )

        for input_pathname_key in config["input_pathnames"].keys():
            if config["input_pathnames"][input_pathname_key] == "DOCKEX_REQUIRED":
                raise ValueError(
                    f'Missing required input pathname "{input_pathname_key}" for job name "{job_name}"'
                )

        for output_pathname_key in config["output_pathnames"].keys():
            config["output_pathnames"][
                output_pathname_key
            ] = f"{module_name}/{job_name}{config['output_pathnames'][output_pathname_key]}"

        if skip_job is False:
            self.job_list.append(copy.deepcopy(config))

        return config["output_pathnames"]

    def archive_project(self):
        self.redis_client.set("status", "ARCHIVING PROJECT")
        self.project_archive_filename = (
            f"project_{self.experiment_name}.zip"
        )  # this assumes we're running in a container or using /tmp/dockex locally
        self.project_archive_pathname = (
            f"/tmp/dockex/data/{self.project_archive_filename}"
        )  # this assumes we're running in a container or using /tmp/dockex locally
        shutil.make_archive(
            self.project_archive_pathname.replace(".zip", ""),
            "zip",
            "/tmp/dockex/project",
        )  # this assumes we're running in a container or using /tmp/dockex locally

        self.redis_client.set("project_archive_filename", self.project_archive_filename)

    def wait_for_jobs_to_end(self):
        keep_waiting = True
        while keep_waiting:
            time.sleep(self.sleep_seconds)

            num_complete_jobs = self.redis_client.get("num_complete_jobs")
            num_total_jobs = self.redis_client.get("num_total_jobs")

            print_progress(num_complete_jobs, num_total_jobs)

            if num_complete_jobs == num_total_jobs:
                keep_waiting = False

    def wait_for_save_outputs(self):
        # make sure output_saver flag is True
        self.redis_client.set("output_saver_working_flag", True)

        # send an experiment done message to output_saver
        # it should set flag to False once it processes this message
        self.redis_client.rpush("output_saver", CLOSE_ZIP_COMMAND)

        # wait for OutputSaver to finish its business
        while self.redis_client.get("output_saver_working_flag") is True:
            pass

    def wait_for_experiment_to_finish(self):
        print("WAITING FOR EXPERIMENT TO FINISH")
        self.redis_client.set("status", "WAITING FOR EXPERIMENT TO FINISH")

        # store the job csv in the experiment zip file
        self.redis_client.rpush("output_saver", self.csv_filename)

        # send extra outputs to output_saver
        for extra_output_pathname in self.extra_output_pathnames:
            self.redis_client.rpush("output_saver", extra_output_pathname)

        if self.save_project:
            self.redis_client.rpush("output_saver", self.project_archive_filename)

        self.wait_for_jobs_to_end()

        # generate a csv of all the finished jobs and add it to the zip
        post_job_list = [
            json.loads(b) for b in self.job_lookup_db.mget(self.job_lookup_db.keys("*"))
        ]
        post_csv_filename = f"post_{self.csv_filename}"
        post_csv_pathname = (
            f"/tmp/dockex/data/{post_csv_filename}"
        )  # this assumes we're running in a container or using /tmp/dockex locally
        pd.DataFrame(post_job_list).sort_values(by="job_num", ascending=True).set_index(
            "name"
        ).to_csv(post_csv_pathname)
        self.redis_client.rpush("output_saver", post_csv_filename)

        self.wait_for_save_outputs()

        os.remove(post_csv_pathname)
        os.remove(self.csv_pathname)
        os.remove(self.project_archive_pathname)

    def initialize_experiment_variables(self):
        # set the global job num for future experiments
        self.redis_client.set("manager_job_num", self.job_num)

        # flush experiment dbs
        self.dependency_lookup_db.flushdb()
        self.dependency_counts_db.flushdb()
        self.job_lookup_db.flushdb()

        # initialize the overall experiment job counts
        self.redis_client.set("num_total_jobs", 0)
        self.redis_client.set("num_pending_jobs", 0)
        self.redis_client.set("num_ready_jobs", 0)
        self.redis_client.set("num_running_jobs", 0)
        self.redis_client.set("num_complete_jobs", 0)
        self.redis_client.set("num_error_jobs", 0)

        self.redis_client.strict_redis.delete("unique_module_paths")

        unique_module_names = self.redis_client.get_list("unique_module_names")
        for unique_module_name in unique_module_names:
            stats_keys = get_module_stats_keys(unique_module_name)

            for key in stats_keys.values():
                self.redis_client.strict_redis.delete(key)
        self.redis_client.strict_redis.delete("unique_module_names")

        ready_jobs_list_key_dicts = self.redis_client.smembers(
            "ready_jobs_list_key_dicts"
        )
        for ready_jobs_list_key_dict in ready_jobs_list_key_dicts:
            self.redis_client.strict_redis.delete(
                ready_jobs_list_key_dict["ready_jobs_list_key"]
            )
        self.redis_client.strict_redis.delete("ready_jobs_list_key_dicts")

        self.redis_client.set("experiment_name", self.experiment_name)

        # reset output_saver just in case a zip was left open
        self.redis_client.rpush("output_saver", CLOSE_ZIP_COMMAND)

        self.redis_client.strict_redis.delete("error_jobs")

    def stage_jobs(self):
        print("STAGING JOBS")
        self.redis_client.set("status", "STAGING JOBS")

        unique_module_names = []
        unique_module_paths = []
        for job in self.job_list:
            input_pathnames = job["input_pathnames"]
            module_name = job["module_name"]
            module_path = job["path"]
            name = job["name"]
            skip_input_pathnames = job["skip_input_pathnames"]

            if module_path not in unique_module_paths:
                unique_module_paths.append(module_path)
                self.redis_client.rpush("unique_module_paths", module_path)

            ready_jobs_list_dict = OrderedDict(
                [
                    ("cpu_credits", job["cpu_credits"]),
                    ("gpu_credits", job["gpu_credits"]),
                ]
            )

            # register the ready_jobs list that corresponds to this job's credits
            ready_jobs_list_key = ready_jobs_dict_to_key(ready_jobs_list_dict)

            ready_jobs_list_dict["ready_jobs_list_key"] = ready_jobs_list_key

            # this is an ordered dict to guarantee the resulting json string is always in the same order
            # we're using a redis set here, and don't want duplicate entries if dict keys are in different order
            self.redis_client.sadd("ready_jobs_list_key_dicts", ready_jobs_list_dict)

            stats_keys = get_module_stats_keys(module_name)

            if module_name not in unique_module_names:
                unique_module_names.append(module_name)
                self.redis_client.rpush("unique_module_names", module_name)

                # it's important that total_jobs is updated first for accurately detecting experiment completion
                self.redis_client.set(stats_keys["num_total_jobs"], 1)
                self.redis_client.set(stats_keys["num_pending_jobs"], 0)
                self.redis_client.set(stats_keys["num_ready_jobs"], 0)
                self.redis_client.set(stats_keys["num_running_jobs"], 0)
                self.redis_client.set(stats_keys["num_complete_jobs"], 0)
                self.redis_client.set(stats_keys["num_error_jobs"], 0)

            else:
                # it's important that total_jobs is updated first for accurately detecting experiment completion
                self.redis_client.strict_redis.incr(stats_keys["num_total_jobs"])

            num_input_pathnames = 0
            if len(input_pathnames.keys()) > 0:
                for input_pathname_key in input_pathnames.keys():
                    input_pathname = input_pathnames[input_pathname_key]

                    if input_pathname is not None:
                        if (
                            skip_input_pathnames is False
                            or skip_input_pathnames is None
                        ):
                            self.dependency_lookup_db.sadd(input_pathname, name)
                            num_input_pathnames += 1

                        elif skip_input_pathnames is True:
                            pass

                        elif type(skip_input_pathnames) is list:
                            if input_pathname_key in skip_input_pathnames:
                                pass

                            else:
                                self.dependency_lookup_db.sadd(input_pathname, name)
                                num_input_pathnames += 1

            if num_input_pathnames > 0:
                self.dependency_counts_db.set(name, num_input_pathnames)
                self.redis_client.strict_redis.incr(stats_keys["num_pending_jobs"])
                self.redis_client.strict_redis.incr("num_pending_jobs")

            else:
                self.redis_client.rpush(ready_jobs_list_key, job)
                self.redis_client.strict_redis.incr(stats_keys["num_ready_jobs"])
                self.redis_client.strict_redis.incr("num_ready_jobs")

            self.redis_client.strict_redis.incr("num_total_jobs")

            # register the job on the backend
            self.job_lookup_db.set(name, json.dumps(job))

    def set_manager_flag(self):
        print("SETTING MANAGER FLAG")
        self.redis_client.set("status", "SETTING MANAGER FLAG")
        self.redis_client.set("manager_flag", True)

    def unset_manager_flag(self):
        print("UNSETTING MANAGER FLAG")
        self.redis_client.set("status", "UNSETTING MANAGER FLAG")
        self.redis_client.set("manager_flag", False)

    def generate_job_csv(self):
        print("GENERATING JOB CSV")
        pd.DataFrame(self.job_list).to_csv(self.csv_pathname)

    def copy_project(self):
        print("COPYING PROJECT")
        self.redis_client.set("status", "COPYING PROJECT DIRECTORY")
        tmp_project_path = f"{self.tmp_dockex_path}/project"
        empty_make_directory(tmp_project_path)
        copy_tree(self.project_path, tmp_project_path)
        os.system(f"chown -R nonroot:nonroot {tmp_project_path}")

    def acquire_prevent_experiment_overlap_flag(self):
        print("ACQUIRING PREVENT EXPERIMENT OVERLAP FLAG")
        if self.redis_client.get("prevent_experiment_overlap_flag") is True:
            print("WAITING FOR PREVIOUS LOCAL EXPERIMENT TO FINISH")
            while self.redis_client.get("prevent_experiment_overlap_flag") is True:
                pass

        self.redis_client.set("prevent_experiment_overlap_flag", True)

        # TODO: also check and wait for remote machines to prevent overlapping experiments

    def release_prevent_experiment_overlap_flag(self):
        print("RELEASING PREVENT EXPERIMENT OVERLAP FLAG")
        self.redis_client.set("prevent_experiment_overlap_flag", False)

    def run(self, print_build_logs=False):
        print("RUNNING EXPERIMENT")
        self.redis_client.set("status", "RUNNING EXPERIMENT")
        self.generate_job_csv()

        self.acquire_prevent_experiment_overlap_flag()

        start = time.time()

        try:
            self.initialize_experiment_variables()
            self.copy_project()
            self.stage_jobs()

            build_project_modules(
                self.docker_client,
                self.redis_client.get_list("unique_module_paths"),
                print_build_logs=print_build_logs,
                redis_client=self.redis_client,
            )

            self.archive_project()
            self.set_manager_flag()

            self.redis_client.set("status", "RUNNING EXPERIMENT")

            self.wait_for_experiment_to_finish()
            self.unset_manager_flag()

        except:
            self.wait_for_save_outputs()
            self.release_prevent_experiment_overlap_flag()
            self.unset_manager_flag()
            self.redis_client.set("status", "EXPERIMENT FAILED")
            raise

        end = time.time()

        self.release_prevent_experiment_overlap_flag()
        self.redis_client.set("status", "EXPERIMENT COMPLETE")

        print(f"EXPERIMENT EXECUTION TIME: {round((end - start), 2)} seconds")
