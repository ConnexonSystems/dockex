import psutil
import time
import sys
import GPUtil

from core.languages.python.base.PythonJobWithBackend import PythonJobWithBackend


class HardwareMonitor(PythonJobWithBackend):
    def __init__(self, input_args, sleep_seconds=0.25):
        super().__init__(input_args)
        self.sleep_seconds = sleep_seconds

    @staticmethod
    def get_hardware_info():
        virtual_memory = psutil.virtual_memory()

        stats = dict(
            cpu_percent=psutil.cpu_percent(),
            cpu_percent_per_cpu=psutil.cpu_percent(percpu=True),
            cpu_count=psutil.cpu_count(),
            # cpu_freq_current=psutil.cpu_freq().current,
            # cpu_freq_min=psutil.cpu_freq().min,
            # cpu_freq_max=psutil.cpu_freq().max,
            virtual_memory_total=virtual_memory.total,
            virtual_memory_percent=virtual_memory.percent,
            virtual_memory_used=virtual_memory.used,
        )

        gpu_list = GPUtil.getGPUs()

        if len(gpu_list) > 0:
            stats["gpu_count"] = len(gpu_list)
            stats["gpu_percent_per_gpu"] = [
                round(gpu.load * 100.0, 1) for gpu in gpu_list
            ]
            stats["gpu_percent"] = round(
                sum(stats["gpu_percent_per_gpu"]) / stats["gpu_count"], 1
            )
            stats["gpu_memory_total"] = (
                sum([gpu.memoryTotal for gpu in gpu_list]) * 1000000.0
            )
            stats["gpu_memory_used"] = (
                sum([gpu.memoryUsed for gpu in gpu_list]) * 1000000.0
            )
            stats["gpu_memory_percent"] = round(
                stats["gpu_memory_used"] * 100.0 / stats["gpu_memory_total"], 1
            )

        else:
            stats["gpu_count"] = 0
            stats["gpu_percent_per_gpu"] = []
            stats["gpu_percent"] = 0.0
            stats["gpu_memory_total"] = 0.0
            stats["gpu_memory_used"] = 0.0
            stats["gpu_memory_percent"] = 0.0

        return stats

    def run_job(self):
        while True:
            try:
                self.redis_client.set("hardware_monitor", self.get_hardware_info())

            except Exception as e:
                print(e)

            time.sleep(self.sleep_seconds)


if __name__ == "__main__":
    HardwareMonitor(sys.argv).run()
