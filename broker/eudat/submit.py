#!/usr/bin/env python3

import sys

from broker import cfg
from broker.config import env
from broker.eblocbroker.job import Job
from broker.imports import connect
from broker.libs import eudat
from broker.submit_base import SubmitBase
from broker.utils import print_tb

Ebb = cfg.Ebb


def eudat_submit(job_config_fn):
    connect()
    job = Job()
    job.set_config(job_config_fn)
    submit_base = SubmitBase()
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
        provider = Ebb.w3.toChecksumAddress(job.provider_addr)

    job.folders_to_share = job.paths
    submit_base.check_link_folders(job.folders_to_share)
    eudat.submit(provider, requester, job)


if __name__ == "__main__":
    try:
        eudat_submit("/home/alper/ebloc-broker/broker/eudat/job.yaml")
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print_tb(str(e))
