import json
import os
import docker

from core.languages.python.helpers.docker_helpers import build_image_run_container


class DockexBootstrap:
    def __init__(self):
        super().__init__()

    @staticmethod
    def run():
        print("RUNNING DOCKEX BOOTSTRAP")

        docker_client = docker.from_env()

        with open("base_config.json", "r") as f:
            config = json.load(f)

        if os.path.isfile("user_config.json"):
            with open("user_config.json", "r") as f:
                user_config = json.load(f)

            config.update(user_config)

        print("dockex config:")
        print(config)

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
                    config["tmp_dockex_path"]: {"bind": "/tmp/dockex", "mode": "rw"},
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
