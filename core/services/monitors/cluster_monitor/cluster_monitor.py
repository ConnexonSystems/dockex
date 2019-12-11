import time
import sys
import json

from core.languages.python.base.PythonJobWithBackend import PythonJobWithBackend
from core.languages.python.helpers.DockexRedisClient import DockexRedisClient


class ClusterMonitor(PythonJobWithBackend):
    def __init__(self, input_args, sleep_seconds=0.25):
        super().__init__(input_args)
        self.sleep_seconds = sleep_seconds

    def run_job(self):
        while True:
            try:
                dockex_machines = self.redis_client.get_list("dockex_machines")

                cluster_cpu_list = []
                cluster_ram_total_list = []
                cluster_ram_used_list = []

                cluster_gpu_list = []
                cluster_gpu_memory_total_list = []
                cluster_gpu_memory_used_list = []

                cluster_cpu_credits_total = 0
                cluster_cpu_credits_used = 0
                cluster_gpu_credits_total = 0
                cluster_gpu_credits_used = 0

                p = self.redis_client.strict_redis.pipeline()
                p.delete("cluster_monitor")
                p.delete("cluster_stats")

                for dockex_machine in dockex_machines:
                    try:
                        temp_redis_client = DockexRedisClient(
                            dockex_machine["redis_address"]
                        )
                        dockex_machine["hardware_monitor"] = temp_redis_client.get(
                            "hardware_monitor"
                        )
                        dockex_machine["credits_monitor"] = temp_redis_client.get(
                            "credits_monitor"
                        )
                        dockex_machine["status"] = temp_redis_client.get("status")
                        dockex_machine["data_path"] = temp_redis_client.get("data_path")
                        dockex_machine["json_path"] = temp_redis_client.get("json_path")
                        dockex_machine["redis_address"] = temp_redis_client.get(
                            "redis_address"
                        )
                        dockex_machine["webdis_address"] = temp_redis_client.get(
                            "webdis_address"
                        )

                        p.rpush("cluster_monitor", json.dumps(dockex_machine))

                        cluster_cpu_list += dockex_machine["hardware_monitor"][
                            "cpu_percent_per_cpu"
                        ]
                        cluster_ram_total_list.append(
                            dockex_machine["hardware_monitor"]["virtual_memory_total"]
                        )
                        cluster_ram_used_list.append(
                            dockex_machine["hardware_monitor"]["virtual_memory_used"]
                        )

                        cluster_gpu_list += dockex_machine["hardware_monitor"][
                            "gpu_percent_per_gpu"
                        ]
                        cluster_gpu_memory_total_list.append(
                            dockex_machine["hardware_monitor"]["gpu_memory_total"]
                        )
                        cluster_gpu_memory_used_list.append(
                            dockex_machine["hardware_monitor"]["gpu_memory_used"]
                        )

                        cluster_cpu_credits_total += dockex_machine["credits_monitor"][
                            "cpu_credits_total"
                        ]
                        cluster_cpu_credits_used += dockex_machine["credits_monitor"][
                            "cpu_credits_used"
                        ]

                        cluster_gpu_credits_total += dockex_machine["credits_monitor"][
                            "gpu_credits_total"
                        ]
                        cluster_gpu_credits_used += dockex_machine["credits_monitor"][
                            "gpu_credits_used"
                        ]

                    except Exception as e:
                        print(e)

                cluster_num_cpus = len(cluster_cpu_list)
                if cluster_num_cpus > 0:
                    cluster_cpu_utilization = round(
                        sum(cluster_cpu_list) / float(cluster_num_cpus), 1
                    )
                else:
                    cluster_cpu_utilization = 0.0

                cluster_num_gpus = len(cluster_gpu_list)
                if cluster_num_gpus > 0:
                    cluster_gpu_utilization = round(
                        sum(cluster_gpu_list) / float(cluster_num_gpus), 1
                    )
                else:
                    cluster_gpu_utilization = 0.0

                virtual_memory_total = sum(cluster_ram_total_list)
                virtual_memory_used = sum(cluster_ram_used_list)
                if virtual_memory_total > 0.0:
                    virtual_memory_percent = round(
                        (virtual_memory_used * 100.0 / virtual_memory_total), 1
                    )
                else:
                    virtual_memory_percent = 0.0

                gpu_memory_total = sum(cluster_gpu_memory_total_list)
                gpu_memory_used = sum(cluster_gpu_memory_used_list)
                if gpu_memory_total > 0.0:
                    gpu_memory_percent = round(
                        (gpu_memory_used * 100.0 / gpu_memory_total), 1
                    )
                else:
                    gpu_memory_percent = 0.0

                cluster_stats = {
                    "machine_count": len(dockex_machines),
                    "cpu_count": cluster_num_cpus,
                    "cpu_percent": cluster_cpu_utilization,
                    "cpu_percent_per_cpu": cluster_cpu_list,
                    "virtual_memory_total": virtual_memory_total,
                    "virtual_memory_used": virtual_memory_used,
                    "virtual_memory_percent": virtual_memory_percent,
                    "gpu_count": cluster_num_gpus,
                    "gpu_percent": cluster_gpu_utilization,
                    "gpu_percent_per_gpu": cluster_gpu_list,
                    "gpu_memory_total": gpu_memory_total,
                    "gpu_memory_used": gpu_memory_used,
                    "gpu_memory_percent": gpu_memory_percent,
                    "cpu_credits_total": cluster_cpu_credits_total,
                    "cpu_credits_used": cluster_cpu_credits_used,
                    "gpu_credits_total": cluster_gpu_credits_total,
                    "gpu_credits_used": cluster_gpu_credits_used,
                }

                p.set("cluster_stats", json.dumps(cluster_stats))

                p.execute()

            except Exception as e:
                print(e)

            time.sleep(self.sleep_seconds)


if __name__ == "__main__":
    ClusterMonitor(sys.argv).run()
