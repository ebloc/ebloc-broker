#!/usr/bin/env python3

from broker.eblocbroker.job import Job
import sys

import broker.libs.eudat as eudat
from broker.config import env
from broker.imports import connect
from broker.utils import print_tb
import broker.cfg as cfg


Ebb = cfg.Ebb


def main():
    connect()
    job = Job()
    oc_requester = "059ab6ba-4030-48bb-b81b-12115f531296"
    requester = Ebb.w3.toChecksumAddress("0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49")
    try:
        job.check_account_status(requester)
    except Exception as e:
        print_tb(e)
        raise e

    eudat.login(oc_requester, env.LOG_PATH.joinpath(".eudat_client.txt"), env.OC_CLIENT_REQUESTER)
    if len(sys.argv) == 3:
        provider = str(sys.argv[1])
        tar_hash = sys.argv[2]
        print(f"==> provided_hash={tar_hash}")
    else:
        # provider = "0x57b60037b82154ec7149142c606ba024fbb0f991"  # netlab
        provider = "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49"  # home2-vm

    folders_to_share = []  # full path of the code or data should be provided
    data_folders = {}
    source_code_dir = env.BASE_DATA_PATH / "test_data" / "base" / "source_code"
    data_folders[0] = env.BASE_DATA_PATH / "test_data" / "base" / "data" / "data1"
    folders_to_share.append(source_code_dir)
    folders_to_share.append(data_folders[0])
    eudat.submit(provider, requester, folders_to_share)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print_tb(str(e))
