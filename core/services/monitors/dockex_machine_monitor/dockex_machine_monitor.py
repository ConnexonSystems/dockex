import time
import sys
import json
import redis

from core.languages.python.base.PythonJobWithBackend import PythonJobWithBackend
from core.languages.python.helpers.DockexRedisClient import DockexRedisClient


class DockexMachineIdentifier(PythonJobWithBackend):
    def __init__(self, input_args, sleep_seconds=1.0):
        super().__init__(input_args)
        self.sleep_seconds = sleep_seconds

    def run_job(self):
        while True:
            try:
                dockex_redis_addresses = self.redis_client.smembers(
                    "dockex_redis_addresses"
                )

                p = self.redis_client.strict_redis.pipeline()
                p.delete("dockex_machines")

                for dockex_redis_address in dockex_redis_addresses:
                    try:
                        temp_client = DockexRedisClient(dockex_redis_address)

                        dockex_status_dict = dict(
                            machine_name=temp_client.get("machine_name"),
                            redis_address=dockex_redis_address,
                            manager_flag=temp_client.get("manager_flag"),
                            experiment_name=temp_client.get("experiment_name"),
                            ip_address=temp_client.get("ip_address"),
                            tmp_dockex_ftpd_port=temp_client.get(
                                "tmp_dockex_ftpd_port"
                            ),
                            tmp_dockex_ftpd_password=temp_client.get(
                                "tmp_dockex_ftpd_password"
                            ),
                        )

                        p.rpush("dockex_machines", json.dumps(dockex_status_dict))

                    except redis.exceptions.ConnectionError:
                        pass

                p.execute()

            except Exception as e:
                print(e)

            time.sleep(self.sleep_seconds)


if __name__ == "__main__":
    DockexMachineIdentifier(sys.argv).run()
