#!/usr/bin/env python3

from broker.link import check_link_folders
import sys

from broker import cfg
from broker._utils._log import log
from broker.config import env
from broker.eblocbroker.job import Job
from broker.imports import connect
from broker.libs import eudat
from broker.utils import print_tb


def eudat_submit(job: Job):
    Ebb = cfg.Ebb
    requester = Ebb.w3.toChecksumAddress("0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49")
    connect()
    oc_requester = "059ab6ba-4030-48bb-b81b-12115f531296"
    try:
        job.check_account_status(requester)
    except Exception as e:
        print_tb(e)
        raise e

    eudat.login(oc_requester, env.LOG_PATH.joinpath(".eudat_client.txt"), env.OC_CLIENT_REQUESTER)
    if len(sys.argv) == 3:
        provider = str(sys.argv[1])
        tar_hash = sys.argv[2]
        log(f"==> provided_hash={tar_hash}")
    else:
        provider = Ebb.w3.toChecksumAddress(job.provider_addr)

    job.folders_to_share = job.paths
    check_link_folders(job.folders_to_share)
    eudat.submit(provider, requester, job)


if __name__ == "__main__":
    try:
        job = Job()
        job.set_config("/home/alper/ebloc-broker/broker/eudat/job.yaml")
        eudat_submit(job)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print_tb(str(e))
