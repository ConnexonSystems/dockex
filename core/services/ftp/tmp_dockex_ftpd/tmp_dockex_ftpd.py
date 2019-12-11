import sys
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import MultiprocessFTPServer
import resource
import secrets

from core.languages.python.base.PythonJobWithBackend import PythonJobWithBackend


class TmpDockexFTPD(PythonJobWithBackend):
    def __init__(self, input_args):
        super().__init__(input_args)
        self.port = self.redis_client.get("tmp_dockex_ftpd_port")
        self.ip_address = self.redis_client.get("ip_address")

    def run_job(self):
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, (hard, hard))

        password = secrets.token_hex(32)

        # TODO: find a better way to enable automatic cluster creation
        # TODO: or require password authentication for accessing redis/webdis
        self.redis_client.set("tmp_dockex_ftpd_password", password)

        authorizer = DummyAuthorizer()
        authorizer.add_user("dockex", password, self.params["path"], perm="elradfmwMT")
        handler = FTPHandler
        handler.authorizer = authorizer
        server = MultiprocessFTPServer((self.ip_address, self.port), handler)

        server.max_cons = 0

        server.serve_forever()


if __name__ == "__main__":
    TmpDockexFTPD(sys.argv).run()
