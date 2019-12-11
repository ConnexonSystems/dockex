import os
import shutil


def empty_make_directory(path):
    if os.path.isdir(path):
        try:
            shutil.rmtree(path)
        except FileNotFoundError:  # in case of race condition
            pass

    try:
        os.makedirs(path)
    except FileExistsError:  # in case of race condition
        pass


def check_make_directory(path):
    if not os.path.isdir(path):
        try:
            os.makedirs(path)
        except FileExistsError:  # in case of race condition
            pass


def empty_directory(path):
    for filename in os.listdir(path):
        filepath = os.path.join(path, filename)

        try:
            shutil.rmtree(filepath)
        except OSError:
            os.remove(filepath)
