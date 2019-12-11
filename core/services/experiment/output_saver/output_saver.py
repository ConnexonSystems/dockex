import sys
import zipfile
import os

from core.languages.python.base.ListPopService import ListPopService
from core.experiment.helpers.ftp_find_file import ftp_find_file


CLOSE_ZIP_COMMAND = "DOCKEX_OUTPUT_SAVER_CLOSE_ZIP"


class OutputSaver(ListPopService):
    def __init__(self, input_args):
        super().__init__(input_args, "output_saver")

        self.zip_handler = None
        self.data_path = "/tmp/dockex/data"

        self.redis_client.set("output_saver_working_flag", False)

    def pop_callback(self, save_output_pathname):
        if save_output_pathname == CLOSE_ZIP_COMMAND:
            if self.zip_handler is not None:
                self.zip_handler.close()
                self.zip_handler = None

            # release the OutputSaver flag so Managers know there is no pending zip
            self.redis_client.set("output_saver_working_flag", False)

        else:
            # if the zip hasn't been created, create one
            if self.zip_handler is None:
                experiment_name = self.redis_client.get("experiment_name")

                if experiment_name is not None:
                    zip_name = f"{self.data_path}/{experiment_name}.zip"
                    self.zip_handler = zipfile.ZipFile(
                        zip_name, "w", zipfile.ZIP_DEFLATED, allowZip64=True
                    )

                    # set OutputSaver flag so Managers know there's a pending zip
                    self.redis_client.set("output_saver_working_flag", True)

                else:
                    raise ValueError(
                        "experiment_name must be set by ExperimentManager before files can be saved"
                    )

            local_save_output_pathname = self.data_path + "/" + save_output_pathname

            # if the file isn't local, go find it
            if not os.path.isfile(local_save_output_pathname):
                # TODO: this could be optimized more, currently connecting/disconnecting to servers for each output file
                found_file = ftp_find_file(
                    self.redis_client.get_list("dockex_machines"),
                    self.redis_client.get("ip_address"),
                    f"data/{save_output_pathname}",
                    local_save_output_pathname,
                )

            else:
                found_file = True

            if found_file:
                self.zip_handler.write(
                    local_save_output_pathname, arcname=save_output_pathname
                )


if __name__ == "__main__":
    OutputSaver(sys.argv).run()
