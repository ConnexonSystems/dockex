import time
from ftplib import FTP


def connect_ftp_clients(ftp_server_dicts, local_ip_address):

    ftp_clients = []

    for ftp_server_dict in ftp_server_dicts:
        ftp_client = connect_ftp_client(ftp_server_dict, local_ip_address)
        if ftp_client:
            ftp_clients.append(ftp_client)

    return ftp_clients


def connect_ftp_client(ftp_server_dict, local_ip_address):
    keep_trying = True
    while keep_trying:
        try:
            if ftp_server_dict["ip_address"] == local_ip_address:
                ftp_client = None
                # ftp_client = FTP('')
                # ftp_clients.append(ftp_client)
                # print('DEBUG')
                pass
            else:
                print("CONNECTING TO: " + str(ftp_server_dict))
                ftp_client = FTP("")
                # TODO: maybe this timeout is getting hit during the file transfer
                # TODO: problem was that we have problems connecting if we don't have this value set I think
                # TODO: could try increasing it, or removing it (which sets to global max value) and see if it breaks again like with DemoJob
                # ftp_client.connect(ftp_server_dict['ip_address'], ftp_server_dict['tmp_dockex_ftpd_port'], timeout=20)
                ftp_client.connect(
                    ftp_server_dict["ip_address"],
                    ftp_server_dict["tmp_dockex_ftpd_port"],
                    timeout=120,
                )
                print("LOGGING IN")
                ftp_client.login("dockex", ftp_server_dict["tmp_dockex_ftpd_password"])
                print("LOGGED IN")

            keep_trying = False
        except Exception as e:
            print("ERROR CONNECTING TO FTP SERVER:")
            print(ftp_server_dict)
            print(e)
            time.sleep(1.0)

    return ftp_client
