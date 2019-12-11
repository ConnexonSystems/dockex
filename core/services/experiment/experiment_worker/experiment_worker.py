import sys
import json
import time
import pandas as pd
import numpy as np
import docker
import zipfile

from core.languages.python.base.PythonJobWithBackend import PythonJobWithBackend
from core.languages.python.helpers.DockexRedisClient import DockexRedisClient
from core.languages.python.helpers.docker_helpers import build_project_modules
from core.experiment.helpers.ftp_find_file import ftp_find_file
from core.languages.python.helpers.path_helpers import empty_directory


class ExperimentWorker(PythonJobWithBackend):
    def __init__(
        self, input_args, checking_manager_sleep_seconds=0.5, working_sleep_seconds=0.25
    ):
        super().__init__(input_args)

        self.checking_manager_sleep_seconds = checking_manager_sleep_seconds
        self.working_sleep_seconds = working_sleep_seconds

        self.docker_client = docker.from_env()

        self.experiment_manager = None
        self.experiment_manager_dict = None

    def run_job(self):
        while True:
            # check if we're connected to a manager
            # if we're NOT connected to a manager
            if self.experiment_manager is None:
                # check if there are any managers available
                dockex_machines_df = pd.DataFrame(
                    self.redis_client.get_list("dockex_machines")
                )

                if len(dockex_machines_df) > 0:
                    manager_machines_df = dockex_machines_df.loc[
                        dockex_machines_df.manager_flag == True
                    ]

                    if len(manager_machines_df) > 0:
                        # if so, connect to the manager
                        self.experiment_manager_dict = manager_machines_df.iloc[
                            0
                        ].to_dict()
                        self.experiment_manager = DockexRedisClient(
                            self.experiment_manager_dict["redis_address"]
                        )
                        self.redis_client.set(
                            "manager_redis_address",
                            self.experiment_manager_dict["redis_address"],
                        )

                        # if the manager is not the local manager
                        if (
                            self.experiment_manager_dict["redis_address"]
                            != self.redis_address
                        ):
                            # empty the project directory
                            empty_directory("/tmp/dockex/project")
                            empty_directory("/tmp/dockex/data")

                            # need to copy project archive, unarchive it, and build module images
                            project_archive_filename = self.experiment_manager.get(
                                "project_archive_filename"
                            )
                            local_project_archive_filename = (
                                f"/tmp/dockex/data/{project_archive_filename}"
                            )

                            found_project_archive = ftp_find_file(
                                self.experiment_manager.get_list("dockex_machines"),
                                self.redis_client.get("ip_address"),
                                f"data/{project_archive_filename}",
                                local_project_archive_filename,
                            )

                            if found_project_archive:
                                with zipfile.ZipFile(
                                    local_project_archive_filename, "r"
                                ) as zip_file:
                                    zip_file.extractall("/tmp/dockex/project")

                                # build the module images
                                experiment_module_paths = self.experiment_manager.get_list(
                                    "unique_module_paths"
                                )
                                # TODO: need a way to signal to the experiment that a build failed
                                # TODO: maybe a flag on manager that the experiment continually checks
                                # TODO: or maybe manager needs to test build before setting manager flag?
                                # TODO: even then though, if a build fails on remote host, that host should NOT work on that experiment name
                                # TODO: maybe a worker should track bad experiment names
                                self.redis_client.set(
                                    "status", "BUILDING PROJECT MODULES"
                                )
                                build_project_modules(
                                    self.docker_client, experiment_module_paths
                                )

                            else:
                                self.experiment_manager_dict = None
                                self.experiment_manager = None
                                self.redis_client.strict_redis.delete(
                                    "manager_redis_address"
                                )

                    else:
                        time.sleep(self.checking_manager_sleep_seconds)
                else:
                    time.sleep(self.checking_manager_sleep_seconds)

            # if we are connected to a manager
            else:
                # check if the manager is still a manager
                # if it is NOT still a manager
                if self.experiment_manager.get("manager_flag") is not True:
                    # disconnect from the manager
                    self.experiment_manager_dict = None
                    self.experiment_manager = None
                    self.redis_client.strict_redis.delete("manager_redis_address")

                # if it is still a manager
                else:
                    # check that the experiment name is the same
                    # if it is NOT the same, a new experiment has started
                    if (
                        self.experiment_manager.get("experiment_name")
                        != self.experiment_manager_dict["experiment_name"]
                    ):
                        # disconnect from the manager
                        self.experiment_manager_dict = None
                        self.experiment_manager = None
                        self.redis_client.strict_redis.delete("manager_redis_address")

                    # if the experiment name is the same
                    else:
                        # see if we can pull any work to do
                        # get the list of ready_jobs lists
                        ready_jobs_df = pd.DataFrame(
                            self.experiment_manager.smembers(
                                "ready_jobs_list_key_dicts"
                            )
                        )

                        if len(ready_jobs_df) > 0:
                            # start with the jobs requiring the most credits
                            ready_jobs_df = ready_jobs_df.sort_values(
                                by=["gpu_credits", "cpu_credits"], ascending=False
                            )

                            num_open_cpu_credits = self.redis_client.get(
                                "cpu_credits_total"
                            ) - self.redis_client.get("cpu_credits_used")
                            num_open_gpu_credits = self.redis_client.get(
                                "gpu_credits_total"
                            ) - self.redis_client.get("gpu_credits_used")

                            if num_open_cpu_credits > 0 or num_open_gpu_credits > 0:
                                for ready_jobs_df_ind in ready_jobs_df.index:
                                    num_open_cpu_credits = self.redis_client.get(
                                        "cpu_credits_total"
                                    ) - self.redis_client.get("cpu_credits_used")
                                    num_open_gpu_credits = self.redis_client.get(
                                        "gpu_credits_total"
                                    ) - self.redis_client.get("gpu_credits_used")

                                    required_cpu_credits = int(
                                        ready_jobs_df.loc[
                                            ready_jobs_df_ind, "cpu_credits"
                                        ]
                                    )
                                    required_gpu_credits = int(
                                        ready_jobs_df.loc[
                                            ready_jobs_df_ind, "gpu_credits"
                                        ]
                                    )
                                    ready_jobs_key = ready_jobs_df.loc[
                                        ready_jobs_df_ind, "ready_jobs_list_key"
                                    ]

                                    slots_min_list = []
                                    if required_cpu_credits > 0:
                                        num_open_cpu_slots = int(
                                            np.floor(
                                                num_open_cpu_credits
                                                / required_cpu_credits
                                            )
                                        )
                                        slots_min_list.append(num_open_cpu_slots)

                                    if required_gpu_credits > 0:
                                        num_open_gpu_slots = int(
                                            np.floor(
                                                num_open_gpu_credits
                                                / required_gpu_credits
                                            )
                                        )
                                        slots_min_list.append(num_open_gpu_slots)

                                    num_open_slots = int(np.min(slots_min_list))

                                    if num_open_slots > 0:
                                        p = (
                                            self.experiment_manager.strict_redis.pipeline()
                                        )
                                        p.lrange(
                                            ready_jobs_key, 0, (num_open_slots - 1)
                                        )  # lrange is inclusive, so - 1
                                        p.ltrim(ready_jobs_key, num_open_slots, -1)
                                        pop_job_dicts, _ = p.execute()

                                        if len(pop_job_dicts) > 0:
                                            for pop_job_dict in pop_job_dicts:
                                                pop_job_dict = json.loads(pop_job_dict)
                                                print(pop_job_dict)

                                                # checkout the credits
                                                self.redis_client.strict_redis.incrby(
                                                    "cpu_credits_used",
                                                    required_cpu_credits,
                                                )
                                                self.redis_client.strict_redis.incrby(
                                                    "gpu_credits_used",
                                                    required_gpu_credits,
                                                )

                                                self.redis_client.redis_launch_job(
                                                    f"/tmp/dockex/json/{pop_job_dict['name']}.json",
                                                    pop_job_dict,
                                                )

                        time.sleep(self.working_sleep_seconds)


if __name__ == "__main__":
    ExperimentWorker(sys.argv).run()
