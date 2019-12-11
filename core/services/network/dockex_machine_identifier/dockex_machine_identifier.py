import time
import sys
import redis

from core.languages.python.base.PythonJobWithBackend import PythonJobWithBackend
from core.languages.python.helpers.DockexRedisClient import DockexRedisClient


class DockexMachineIdentifier(PythonJobWithBackend):
    def __init__(self, input_args, sleep_seconds=1.0):
        super().__init__(input_args)
        self.sleep_seconds = sleep_seconds

        self.redis_port = self.redis_client.get("redis_port")
        self.redis_address = self.redis_client.get("redis_address")

    def run_job(self):
        while True:
            try:
                discovered_machine_ips = self.redis_client.get_list(
                    "machines_on_network"
                )

                if len(discovered_machine_ips) > 0:
                    for machine_ip_address in discovered_machine_ips:
                        # this assumes that all cluster machines use same port for redis
                        check_redis_address = (
                            f"http://{machine_ip_address}:{self.redis_port}"
                        )

                        try:
                            if (
                                DockexRedisClient(check_redis_address).get(
                                    "dockex_backend"
                                )
                                is True
                            ):
                                self.redis_client.sadd(
                                    "dockex_redis_addresses", check_redis_address
                                )

                        except (redis.exceptions.ConnectionError, TypeError):
                            self.redis_client.srem(
                                "dockex_redis_addresses", check_redis_address
                            )

                # machine discovery won't pick up local machine if using 127.0.0.1
                # always make sure local machine gets registered
                else:
                    self.redis_client.sadd("dockex_redis_addresses", self.redis_address)

            except Exception as e:
                print(e)

            time.sleep(self.sleep_seconds)


if __name__ == "__main__":
    DockexMachineIdentifier(sys.argv).run()
