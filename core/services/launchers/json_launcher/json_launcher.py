import sys
import docker
import os

from core.languages.python.base.ListPopService import ListPopService
from core.languages.python.helpers.job_config_helpers import read_job_config
from core.languages.python.helpers.docker_helpers import build_image


class JSONLauncher(ListPopService):
    def __init__(self, input_args):
        super().__init__(input_args, "json_launcher")

        self.tmp_dockex_path = self.redis_client.get("tmp_dockex_path")
        self.docker_client = docker.from_env()

        self.build_docker_wrapper_image()

    def build_docker_wrapper_image(self):
        print("BUILDING DOCKER WRAPPER IMAGE")
        build_image(
            self.docker_client,
            dict(
                path=".",
                dockerfile="core/services/launchers/json_launcher/docker_wrapper/Dockerfile",
                tag="docker_wrapper_image",
            ),
            print_build_logs=True,
        )

    def pop_callback(self, json_pathname):
        # json file must be relative to dockex root or to tmp_dockex_path
        if not os.path.isfile(json_pathname):
            check_json_pathname = f"/tmp/dockex/{json_pathname}"

            if os.path.isfile(check_json_pathname):
                json_pathname = check_json_pathname
            else:
                print(f"Could not find json file {json_pathname}")
                return

        job_config = read_job_config(json_pathname)
        name = job_config["name"]
        wrapper_name = f"wrapper_{name}"

        # run docker directly for performance
        os.system(
            (
                f"docker rm -f {wrapper_name} > /dev/null 2>&1; "
                + f"(docker run -d --network host "
                + f"-v {self.tmp_dockex_path}:/tmp/dockex -v /var/run/docker.sock:/var/run/docker.sock "
                + f"--name {wrapper_name} "
                + f"docker_wrapper_image {json_pathname} {self.redis_address} > /dev/null 2>&1 &)"
            )
        )


if __name__ == "__main__":
    JSONLauncher(sys.argv).run()
