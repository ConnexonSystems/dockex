import abc

from core.languages.python.base.PythonJob import PythonJob
from core.languages.python.helpers.DockexRedisClient import DockexRedisClient


class PythonJobWithBackend(PythonJob):
    def __init__(self, input_args):
        super().__init__(input_args)

        self.redis_address = input_args[2]
        self.redis_client = DockexRedisClient(self.redis_address)

    @abc.abstractmethod
    def run_job(self):
        pass
