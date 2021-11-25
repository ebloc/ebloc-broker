#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils._log import log
from broker.config import env
from broker.eblocbroker_scripts.job import Job
from broker.imports import connect
from broker.libs import eudat
from broker.link import check_link_folders
from broker.utils import print_tb


def eudat_submit(job: Job):
    Ebb = cfg.Ebb
    requester = Ebb.w3.toChecksumAddress(job.requester_addr)
    oc_requester = "059ab6ba-4030-48bb-b81b-12115f531296"
    connect()
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
    check_link_folders(job.data_paths, job.registered_data_files)
    return eudat.submit(provider, requester, job)


if __name__ == "__main__":
    try:
        job = Job()
        fn = "job_with_data.yaml"  # "job.yaml"
        job.set_config(fn)
        eudat_submit(job)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print_tb(str(e))