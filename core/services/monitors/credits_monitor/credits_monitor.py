import time
import sys

from core.languages.python.base.PythonJobWithBackend import PythonJobWithBackend


class HardwareMonitor(PythonJobWithBackend):
    def __init__(self, input_args, sleep_seconds=0.25):
        super().__init__(input_args)
        self.sleep_seconds = sleep_seconds

    def run_job(self):
        while True:
            try:
                credits_dict = {
                    "cpu_credits_total": self.redis_client.get("cpu_credits_total"),
                    "cpu_credits_used": self.redis_client.get("cpu_credits_used"),
                    "gpu_credits_total": self.redis_client.get("gpu_credits_total"),
                    "gpu_credits_used": self.redis_client.get("gpu_credits_used"),
                }
                self.redis_client.set("credits_monitor", credits_dict)

            except Exception as e:
                print(e)

            time.sleep(self.sleep_seconds)


if __name__ == "__main__":
    HardwareMonitor(sys.argv).run()
