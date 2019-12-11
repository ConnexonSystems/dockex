import time
import sys
import json
import nmap

from core.languages.python.base.PythonJobWithBackend import PythonJobWithBackend


class MachineDiscovery(PythonJobWithBackend):
    def __init__(self, input_args, sleep_seconds=5.0):
        super().__init__(input_args)
        self.sleep_seconds = sleep_seconds

        self.ip_address = self.redis_client.get("ip_address")
        self.scan_string = ".".join(self.ip_address.split(".")[:-1]) + ".0/24"

    def run_job(self):
        while True:
            try:
                if self.ip_address != "127.0.0.1":
                    network_scanner = nmap.PortScanner()
                    network_scanner.scan(self.scan_string, arguments="-sP -n")
                    machines_on_network = network_scanner.all_hosts()

                    p = self.redis_client.strict_redis.pipeline()
                    p.delete("machines_on_network")

                    if machines_on_network is not None:
                        if len(machines_on_network) > 0:
                            p.rpush(
                                "machines_on_network",
                                *[json.dumps(ip) for ip in machines_on_network]
                            )

                    p.execute()

            except Exception as e:
                print(e)

            time.sleep(self.sleep_seconds)


if __name__ == "__main__":
    MachineDiscovery(sys.argv).run()
