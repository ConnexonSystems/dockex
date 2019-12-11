import uuid
import os
import random

from core.languages.python.helpers.path_helpers import check_make_directory
from core.experiment.helpers.connect_ftp_clients import connect_ftp_client


def ftp_find_file(ftp_server_dicts, worker_ip_address, search_pathname, copy_pathname):

    found_file = False

    # loop through ftp clients, randomly shuffle them to help disperse load, look for file
    for ftp_server_dict in random.sample(ftp_server_dicts, len(ftp_server_dicts)):
        try:
            # wrap everything below the ftp connect in a catch so we can disconnect the client if something goes wrong
            ftp_client = connect_ftp_client(ftp_server_dict, worker_ip_address)

            if ftp_client is not None:
                try:
                    # you have to cwd into the directory where the file is
                    remote_path, remote_file = os.path.split(search_pathname)

                    ftp_client.cwd("/")
                    if remote_path != "":
                        for temp_remote_path in remote_path.split("/"):
                            if temp_remote_path != "":
                                ftp_client.cwd(temp_remote_path)

                    if remote_file in ftp_client.nlst():
                        # then transfer the file
                        # make sure the local directory exists
                        temp_local_path = os.path.split(copy_pathname)[0]
                        check_make_directory(temp_local_path)

                        # to avoid potential collisions, copy file with a uuid filename, then rename to correct filename
                        # os.rename is atomic on linux, also any already open file descriptor links will be safe from garbage collection until they close
                        temp_copy_pathname = (
                            os.path.split(copy_pathname)[0] + "/" + uuid.uuid4().hex
                        )
                        ftp_client.retrbinary(
                            "RETR " + remote_file, open(temp_copy_pathname, "wb").write
                        )
                        os.rename(temp_copy_pathname, copy_pathname)

                        found_file = True

                        ftp_client.close()

                        # stop looking for file
                        break
                    else:
                        ftp_client.close()

                except Exception as e:
                    ftp_client.close()
                    print(e)

        except Exception as e:
            print(e)

    return found_file


def ftp_find_file_from_clients(ftp_clients, search_pathname, copy_pathname):

    found_file = False

    # loop through ftp clients, randomly shuffle them to help disperse load, look for file
    for ftp_client in random.sample(ftp_clients, len(ftp_clients)):
        try:
            # you have to cwd into the directory where the file is
            remote_path, remote_file = os.path.split(search_pathname)

            ftp_client.cwd("/")
            if remote_path != "":
                for temp_remote_path in remote_path.split("/"):
                    if temp_remote_path != "":
                        ftp_client.cwd(temp_remote_path)

            if remote_file in ftp_client.nlst():
                # then transfer the file
                # make sure the local directory exists
                temp_local_path = os.path.split(copy_pathname)[0]
                check_make_directory(temp_local_path)

                # to avoid potential collisions, copy file with a uuid filename, then rename to correct filename
                # os.rename is atomic on linux, also any already open file descriptor links will be safe from garbage collection until they close
                # so I guess this is safe...
                temp_copy_pathname = (
                    os.path.split(copy_pathname)[0] + "/" + uuid.uuid4().hex
                )
                ftp_client.retrbinary(
                    "RETR " + remote_file, open(temp_copy_pathname, "wb").write
                )
                os.rename(temp_copy_pathname, copy_pathname)

                found_file = True

                # stop looking for file
                break

        except Exception as e:
            print(e)

    return found_file
