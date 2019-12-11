import abc
import traceback
import copy

from core.languages.python.helpers.job_config_helpers import read_job_config


class PythonJob(abc.ABC):
    def __init__(self, input_args):
        super().__init__()

        self.json_pathname = input_args[1]

        self.config = read_job_config(self.json_pathname)
        self.name = self.config["name"]

        if "params" in self.config.keys():
            self.params = copy.deepcopy(self.config["params"])
        else:
            self.params = None

    @abc.abstractmethod
    def run_job(self):
        pass

    def run(self):
        print("RUNNING")
        print(f"job name: {self.name}")

        try:
            self.run_job()
        except Exception as e:
            print("ERROR: " + self.name + " - BAD RUN_JOB")
            print(e)
            traceback.print_tb(e.__traceback__)

        print("COMPLETE")
