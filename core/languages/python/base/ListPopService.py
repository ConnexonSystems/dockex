import abc
import json

from core.languages.python.base.PythonJobWithBackend import PythonJobWithBackend


class ListPopService(PythonJobWithBackend):
    def __init__(self, input_args, list_key):
        super().__init__(input_args)

        self.list_key = list_key

    @abc.abstractmethod
    def pop_callback(self, popped):
        pass

    def safe_pop_callback(self, popped):
        try:
            self.pop_callback(popped)

        except Exception as e:
            print(e)
            print("ERROR: pop_callback error with popped value:")
            print(popped)

    def run_job(self):
        while True:
            # block pop
            block_popped = json.loads(
                self.redis_client.strict_redis.blpop(self.list_key)[1]
            )
            self.safe_pop_callback(block_popped)

            # atomically pop the entire list
            p = self.redis_client.strict_redis.pipeline()
            p.lrange(self.list_key, 0, -1)
            p.delete(self.list_key)
            popped_list, _ = p.execute()
            popped_list = [json.loads(s) for s in popped_list]

            # process the popped elements
            for popped in popped_list:
                self.safe_pop_callback(popped)
