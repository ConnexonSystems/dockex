import json
import os

from core.languages.python.helpers.path_helpers import check_make_directory


def read_job_config(pathname):
    with open(pathname, "r") as f:
        config = json.load(f)

    return config


def write_job_config(pathname, config):
    path = os.path.split(pathname)[0]
    check_make_directory(path)

    with open(pathname, "w") as f:
        json.dump(config, f, indent=4)
