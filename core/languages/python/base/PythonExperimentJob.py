import abc
import copy

from core.languages.python.base.PythonJob import PythonJob


class PythonExperimentJob(PythonJob):
    def __init__(self, input_args):
        super().__init__(input_args)

        self.input_pathnames = copy.deepcopy(self.config["input_pathnames"])
        self.output_pathnames = copy.deepcopy(self.config["output_pathnames"])

    @abc.abstractmethod
    def run_job(self):
        pass
