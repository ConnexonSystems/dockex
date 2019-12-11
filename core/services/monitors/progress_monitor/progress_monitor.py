import time
import sys
import pathlib

from core.languages.python.base.PythonJobWithBackend import PythonJobWithBackend
from core.experiment.helpers.get_module_stats_keys import get_module_stats_keys


class ProgressMonitor(PythonJobWithBackend):
    def __init__(self, input_args, sleep_seconds=0.25):
        super().__init__(input_args)
        self.sleep_seconds = sleep_seconds

    def run_job(self):
        while True:
            try:
                unique_module_paths = self.redis_client.get_list("unique_module_paths")

                progress_dict = {
                    "module_progress": [],
                    "total_progress": {
                        "num_complete_jobs": self.redis_client.get("num_complete_jobs"),
                        "num_error_jobs": self.redis_client.get("num_error_jobs"),
                        "num_pending_jobs": self.redis_client.get("num_pending_jobs"),
                        "num_ready_jobs": self.redis_client.get("num_ready_jobs"),
                        "num_running_jobs": self.redis_client.get("num_running_jobs"),
                        "num_total_jobs": self.redis_client.get("num_total_jobs"),
                    },
                    "status": self.redis_client.get("status"),
                }

                if len(unique_module_paths) > 0:
                    module_progress_list = []
                    for module_path in unique_module_paths:
                        module_name = pathlib.PurePath(module_path).name
                        stats_keys = get_module_stats_keys(module_name)

                        module_progress_list.append(
                            {
                                "module_name": module_name,
                                "num_complete_jobs": self.redis_client.get(
                                    stats_keys["num_complete_jobs"]
                                ),
                                "num_error_jobs": self.redis_client.get(
                                    stats_keys["num_error_jobs"]
                                ),
                                "num_pending_jobs": self.redis_client.get(
                                    stats_keys["num_pending_jobs"]
                                ),
                                "num_ready_jobs": self.redis_client.get(
                                    stats_keys["num_ready_jobs"]
                                ),
                                "num_running_jobs": self.redis_client.get(
                                    stats_keys["num_running_jobs"]
                                ),
                                "num_total_jobs": self.redis_client.get(
                                    stats_keys["num_total_jobs"]
                                ),
                            }
                        )

                    progress_dict["module_progress"] = module_progress_list

                self.redis_client.set("progress_monitor", progress_dict)

            except Exception as e:
                print(e)

            time.sleep(self.sleep_seconds)


if __name__ == "__main__":
    ProgressMonitor(sys.argv).run()
