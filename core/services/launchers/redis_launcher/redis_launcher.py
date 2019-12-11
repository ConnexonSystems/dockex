import sys
import uuid

from core.languages.python.base.ListPopService import ListPopService
from core.languages.python.helpers.job_config_helpers import write_job_config


class RedisLauncher(ListPopService):
    def __init__(self, input_args):
        super().__init__(input_args, "redis_launcher")

    def pop_callback(self, redis_launch_params):
        if "json_pathname" not in redis_launch_params.keys():
            json_pathname = f"/tmp/dockex/json/experiment_{uuid.uuid4().hex}.json"
        else:
            json_pathname = redis_launch_params["json_pathname"]

        write_job_config(json_pathname, redis_launch_params["config"])

        self.redis_client.json_launch_job(json_pathname)


if __name__ == "__main__":
    RedisLauncher(sys.argv).run()
