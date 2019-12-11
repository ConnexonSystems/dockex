import json
import socket
import fcntl
import struct
import os
import uuid
import redis
import docker

from core.languages.python.helpers.path_helpers import empty_make_directory
from core.languages.python.helpers.DockexRedisClient import DockexRedisClient
from core.languages.python.helpers.docker_helpers import (
    build_image_run_container,
    build_image,
)


class DockexStartup:
    def __init__(self):
        super().__init__()

        self.config = None
        self.redis_client = None
        self.docker_client = docker.from_env()

    @staticmethod
    def get_ip_address(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(
            fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack("256s", ifname[:15].encode("utf-8")),
            )[20:24]
        )

    def generate_dockex_config(self):
        with open("base_config.json", "r") as f:
            config = json.load(f)

        config["machine_name"] = uuid.uuid4().hex

        if os.path.isfile("user_config.json"):
            with open("user_config.json", "r") as f:
                user_config = json.load(f)

            config.update(user_config)

        # TODO: disable distributed mode for now
        # if "network_interface" in config.keys():
        #     try:
        #         config["ip_address"] = self.get_ip_address(config["network_interface"])
        #
        #     except OSError as e:
        #         print("ERROR: bad network interface")
        #         raise e

        # TODO: disable distributed mode for now
        print(
            "Forcing IP to 127.0.0.1. Distributed mode will be enabled in a future release."
        )
        config["ip_address"] = "127.0.0.1"

        config["redis_address"] = (
            "http://" + config["ip_address"] + ":" + str(config["redis_port"])
        )
        config["webdis_address"] = (
            "http://" + config["ip_address"] + ":" + str(config["webdis_port"])
        )

        config["data_path"] = "/tmp/dockex/data"
        config["json_path"] = "/tmp/dockex/json"
        config["project_path"] = "/tmp/dockex/project"

        dockex_config_pathname = "/tmp/dockex/dockex_config.json"
        with open(dockex_config_pathname, "w") as f:
            json.dump(config, f, indent=4)

        self.config = config

    def create_dockex_directories(self):
        empty_make_directory(self.config["data_path"])
        empty_make_directory(self.config["json_path"])
        empty_make_directory(self.config["project_path"])

    def generate_app_env(self):
        with open("app/.base_env", "r") as f:
            env = f.read()

        env = env.replace(
            "REACT_APP_WEBDIS_ADDRESS=",
            ("REACT_APP_WEBDIS_ADDRESS='" + str(self.config["webdis_address"]) + "'"),
        )
        env = env.replace("PORT=", ("PORT=" + str(self.config["app_port"])))

        with open("/tmp/dockex/.env", "w") as f:
            f.write(env)

    def generate_redis_conf(self):
        base_redis_conf_pathname = "core/services/backend/dockex_redis/base_redis.conf"
        redis_conf_pathname = self.config["tmp_dockex_path"] + "/redis.conf"

        with open(base_redis_conf_pathname, "r") as f:
            data = f.read()

        # replace the ip address and port with dockex_config values
        data = data.replace("127.0.0.1", self.config["ip_address"])
        data = data.replace("6379", str(self.config["redis_port"]))

        # set the number of databases
        data = data.replace("databases 16", "databases 4")

        # turn off saving
        data = data.replace("save 900 1", "# save 900 1")
        data = data.replace("save 300 10", "# save 300 10")
        data = data.replace("save 60 10000", "# save 60 10000")

        # change working directory to tmp_dockex_path
        data = data.replace("dir ./", ("dir " + self.config["tmp_dockex_path"]))

        with open(redis_conf_pathname, "w") as f:
            f.write(data)

    def generate_webdis_json(self):
        webdis_json_pathname = "/tmp/dockex/webdis.json"

        conf = {
            "redis_host": self.config["ip_address"],
            "redis_port": self.config["redis_port"],
            "redis_auth": None,
            "http_host": self.config["ip_address"],
            "http_port": self.config["webdis_port"],
            "threads": 5,
            "pool_size": 20,
            "daemonize": False,
            "websockets": False,
            "database": 0,
            "acl": [
                {"disabled": ["DEBUG"]},
                {"http_basic_auth": "user:password", "enabled": ["DEBUG"]},
            ],
            "verbosity": 6,
            "logfile": "webdis.log",
        }

        with open(webdis_json_pathname, "w") as f:
            json.dump(conf, f, indent=4)

    def initialize(self):
        print("INITIALIZING")
        self.generate_dockex_config()
        self.create_dockex_directories()
        self.generate_app_env()
        self.generate_redis_conf()
        self.generate_webdis_json()

        # change owner of dockex tmp directory to nonroot
        # startup must be root to launch sibling docker containers
        os.system("chown -R nonroot:nonroot /tmp/dockex")

    def launch_redis(self):
        print("BUILDING AND RUNNING REDIS")

        build_image_run_container(
            self.docker_client,
            dict(
                path=".",
                dockerfile="core/services/backend/dockex_redis/Dockerfile",
                tag="dockex_redis_image",
            ),
            dict(
                image="dockex_redis_image",
                name="dockex_redis",
                detach=True,
                network_mode="host",
                volumes={
                    self.config["tmp_dockex_path"]: {
                        "bind": "/tmp/dockex",
                        "mode": "rw",
                    }
                },
            ),
            print_build_logs=True,
        )

        # connect to redis and flush
        self.redis_client = DockexRedisClient(self.config["redis_address"])

        trying_to_connect = True
        while trying_to_connect:
            try:
                self.redis_client.flushdb()
                trying_to_connect = False

            except redis.exceptions.ConnectionError:
                pass

        # fill redis with dockex config values
        for key in self.config.keys():
            self.redis_client.set(key, self.config[key])

        # mark the redis instance as a dockex backend
        self.redis_client.set("dockex_backend", True)

        self.redis_client.set("status", "LAUNCHED REDIS")

    def launch_webdis(self):
        print("LAUNCHING WEBDIS")
        build_image_run_container(
            self.docker_client,
            dict(
                path=".",
                dockerfile="core/services/backend/dockex_webdis/Dockerfile",
                tag="dockex_webdis_image",
            ),
            dict(
                image="dockex_webdis_image",
                name="dockex_webdis",
                detach=True,
                network_mode="host",
                volumes={
                    self.config["tmp_dockex_path"]: {
                        "bind": "/tmp/dockex",
                        "mode": "rw",
                    }
                },
            ),
            print_build_logs=True,
        )

        self.redis_client.set("status", "LAUNCHED WEBDIS")

    def initialize_experiment_variables(self):
        print("INITIALIZING EXPERIMENT VARIABLES")

        # initialize count for ExperimentManagers
        self.redis_client.set("manager_job_num", 0)

        # initialize the overall experiment job counts
        self.redis_client.set("num_total_jobs", 0)
        self.redis_client.set("num_pending_jobs", 0)
        self.redis_client.set("num_ready_jobs", 0)
        self.redis_client.set("num_running_jobs", 0)
        self.redis_client.set("num_complete_jobs", 0)
        self.redis_client.set("num_error_jobs", 0)

        # initialize machine as not a manager
        self.redis_client.set("manager_flag", False)

        # initialize credits
        self.redis_client.set("cpu_credits_total", 0)
        self.redis_client.set("cpu_credits_used", 0)
        self.redis_client.set("gpu_credits_total", 0)
        self.redis_client.set("gpu_credits_used", 0)

        self.redis_client.set("status", "INITIALIZED EXPERIMENT VARIABLES")

    def launch_json_launcher(self):
        print("LAUNCHING JSON LAUNCHER")

        build_image_run_container(
            self.docker_client,
            dict(
                path=".",
                dockerfile="core/services/launchers/json_launcher/Dockerfile",
                tag="json_launcher_image",
            ),
            dict(
                image="json_launcher_image",
                name="json_launcher",
                command=f"core/services/launchers/json_launcher/json_launcher.json {self.config['redis_address']}",
                detach=True,
                network_mode="host",
                volumes={
                    self.config["tmp_dockex_path"]: {
                        "bind": "/tmp/dockex",
                        "mode": "rw",
                    },
                    "/var/run/docker.sock": {
                        "bind": "/var/run/docker.sock",
                        "mode": "rw",
                    },
                },
            ),
            print_build_logs=True,
        )

        self.redis_client.set("status", "LAUNCHED DOCKER LAUNCHER")

    def launch_services(self):
        print("LAUNCHING SERVICES")

        self.redis_client.json_launch_job(
            "core/services/frontend/app_server/app_server.json"
        )

        self.redis_client.json_launch_job(
            "core/services/launchers/redis_launcher/redis_launcher.json"
        )

        self.redis_client.json_launch_job(
            "core/services/monitors/hardware_monitor/hardware_monitor.json"
        )
        self.redis_client.json_launch_job(
            "core/services/monitors/credits_monitor/credits_monitor.json"
        )
        self.redis_client.json_launch_job(
            "core/services/monitors/dockex_machine_monitor/dockex_machine_monitor.json"
        )
        self.redis_client.json_launch_job(
            "core/services/monitors/cluster_monitor/cluster_monitor.json"
        )
        self.redis_client.json_launch_job(
            "core/services/monitors/progress_monitor/progress_monitor.json"
        )

        self.redis_client.json_launch_job(
            "core/services/network/machine_discovery/machine_discovery.json"
        )
        self.redis_client.json_launch_job(
            "core/services/network/dockex_machine_identifier/dockex_machine_identifier.json"
        )

        # TODO: disable distributed mode for now
        # only run ftpd if running distributed
        # if self.config['ip_address'] != "127.0.0.1":
        #     self.redis_client.json_launch_job("core/services/ftp/tmp_dockex_ftpd/tmp_dockex_ftpd.json")

        self.redis_client.json_launch_job(
            "core/services/experiment/output_saver/output_saver.json"
        )
        self.redis_client.json_launch_job(
            "core/services/experiment/experiment_worker/experiment_worker.json"
        )
        self.redis_client.json_launch_job(
            "core/services/experiment/decrement_dependency/decrement_dependency.json"
        )
        self.redis_client.json_launch_job(
            "core/services/experiment/credits_updater/credits_updater.json"
        )

    def build_dockex_experiment_image(self):
        print("Building dockex experiment image")
        build_image(
            self.docker_client,
            dict(
                path=".",
                dockerfile=f"core/experiment/dockex_experiment/Dockerfile",
                tag="dockex_experiment_image",
            ),
            print_build_logs=True,
        )

    def run(self):
        print("DOCKEX STARTUP")

        self.initialize()
        self.launch_redis()
        self.launch_webdis()
        self.initialize_experiment_variables()
        self.build_dockex_experiment_image()
        self.launch_json_launcher()
        self.launch_services()

        self.redis_client.set("status", "READY")


if __name__ == "__main__":
    DockexStartup().run()
