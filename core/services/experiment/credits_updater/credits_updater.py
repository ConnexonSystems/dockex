import sys

from core.languages.python.base.ListPopService import ListPopService
from core.languages.python.helpers.DockexRedisClient import DockexRedisClient


class CreditsUpdater(ListPopService):
    def __init__(self, input_args):
        super().__init__(input_args, "credits_updater")

    def pop_callback(self, credits_update):
        if credits_update["mode"] == "incr":
            DockexRedisClient(credits_update["redis_address"]).strict_redis.incr(
                f"{credits_update['type']}_credits_total"
            )
        elif credits_update["mode"] == "decr":
            DockexRedisClient(credits_update["redis_address"]).strict_redis.decr(
                f"{credits_update['type']}_credits_total"
            )

        elif credits_update["mode"] == "set":
            DockexRedisClient(credits_update["redis_address"]).strict_redis.set(
                f"{credits_update['type']}_credits_total", credits_update["value"]
            )


if __name__ == "__main__":
    CreditsUpdater(sys.argv).run()
