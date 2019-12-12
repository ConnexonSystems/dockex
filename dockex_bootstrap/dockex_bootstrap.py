import json
import os
import docker

from core.languages.python.helpers.docker_helpers import build_image_run_container


class DockexBootstrap:
    def __init__(self):
        super().__init__()

        self.config = None
        self.distributed_verified = False

    def verify_distributed(self):
        if self.distributed_verified is False:
            print('#####################################################################')
            print('######################## CONFIRM DISTRIBUTED ########################')
            print('#####################################################################')

            ask_again = True
            while ask_again:
                
                configuration = f"Dockex IP address : {self.config['ip_address']}"
                
                if 'network_interface' in self.config.keys():
                    configuration = f"Dockex network interface : {self.config['network_interface']}"

                prompt_string = ("\nYou have configured Dockex in distributed mode.\n" +
                                 "This configuration should only be used on secure local networks due to security implications.\n\n" +
                                 "Your current Dockex network configuration is shown below.\n\n" +
                                 f"{configuration}\n\n" +
                                 "Please confirm Dockex launch in distributed mode. [yes / no]  :  ")

                response = input(prompt_string)

                response = response.lower().strip()

                if response not in ['yes', 'no', 'y', 'n']:
                    print('\nInvalid input.')

                else:
                    if response in ['yes', 'y']:
                        self.distributed_verified = True
                        print("\nDistributed mode confirmed.\n")

                    else:
                        exit("\nDistributed mode not confirmed. Aborting bootstrap.\n")

                    ask_again = False

    def run(self):
        print("RUNNING DOCKEX BOOTSTRAP")

        docker_client = docker.from_env()

        with open("base_config.json", "r") as f:
            self.config = json.load(f)

        if os.path.isfile("user_config.json"):
            with open("user_config.json", "r") as f:
                user_config = json.load(f)

            self.config.update(user_config)

        print("dockex self.config:")
        print(self.config)
        print("\n\n")

        if 'force_distributed' in self.config.keys():
            print("FORCE DISTRIBUTED FLAG DETECTED - BYPASSING DISTRIBUTED VERIFICATION \n\n")
            self.distributed_verified = True

        if self.config['ip_address'] != '127.0.0.1':
            self.verify_distributed()

        if 'network_interface' in self.config.keys():
            if self.config['network_interface'] != 'lo':
                self.verify_distributed()

        print("BUILDING AND RUNNING DOCKEX STARTUP")

        build_image_run_container(
            docker_client,
            dict(
                path=".",
                dockerfile="core/dockex_startup/Dockerfile",
                tag="dockex_startup_image",
            ),
            dict(
                image="dockex_startup_image",
                name="dockex_startup",
                detach=True,
                network_mode="host",
                volumes={
                    self.config["tmp_dockex_path"]: {"bind": "/tmp/dockex", "mode": "rw"},
                    "/var/run/docker.sock": {
                        "bind": "/var/run/docker.sock",
                        "mode": "rw",
                    },
                },
            ),
            print_build_logs=True,
        )

        print("COMPLETE")


if __name__ == "__main__":
    DockexBootstrap().run()
