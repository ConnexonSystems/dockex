import json
import redis


class DockexRedisClient:
    def __init__(self, address):
        self.address = address
        split_address = self.address.split(":")
        self.ip_address = split_address[1][2:]
        self.port = split_address[2]

        self.strict_redis = redis.StrictRedis(
            host=self.ip_address, port=self.port, db=0
        )

    def get(self, key):
        val = self.strict_redis.get(key)

        if val:
            return json.loads(val)
        else:
            return val

    def lpop(self, key):
        val = self.strict_redis.lpop(key)

        if val:
            return json.loads(val)
        else:
            return val

    def set(self, key, value):
        return self.strict_redis.set(key, json.dumps(value))

    def rpush(self, key, value):
        return self.strict_redis.rpush(key, json.dumps(value))

    def lrange(self, key, start_ind, end_ind):
        return [
            json.loads(s.decode("utf-8"))
            for s in self.strict_redis.lrange(key, start_ind, end_ind)
        ]

    def sadd(self, key, value):
        return self.strict_redis.sadd(key, json.dumps(value))

    def srem(self, key, value):
        return self.strict_redis.srem(key, json.dumps(value))

    def smembers(self, key):
        return [json.loads(s.decode("utf-8")) for s in self.strict_redis.smembers(key)]

    def flushdb(self):
        self.strict_redis.flushdb()

    def get_list(self, key, start=0, end=-1):
        res = self.strict_redis.lrange(key, start, end)

        if res:
            res = [json.loads(d) for d in res]

        return res

    def json_launch_job(self, json_pathname):
        return self.strict_redis.rpush("json_launcher", json.dumps(json_pathname))

    def redis_launch_job(self, json_pathname, config):
        return self.strict_redis.rpush(
            "redis_launcher",
            json.dumps({"json_pathname": json_pathname, "config": config}),
        )
