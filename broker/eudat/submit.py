#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils._log import log
from broker.config import env
from broker.eblocbroker_scripts.job import Job
from broker.imports import connect
from broker.libs.eudat import login, submit
from broker.link import check_link_folders
from broker.utils import print_tb


def submit_eudat(job: Job, is_pass=False, required_confs=1):
    log("==> Submitting source code through [blue]EUDAT[/blue]")
    Ebb = cfg.Ebb
    requester = Ebb.w3.toChecksumAddress(job.requester_addr)
    oc_client = env.OC_USER
    connect()
    try:
        job.check_account_status(requester)
    except Exception as e:
        print_tb(e)
        raise e

    login(oc_client, env.LOG_PATH.joinpath(".eudat_client.txt"), env.OC_CLIENT)
    if len(sys.argv) == 3:
        provider = str(sys.argv[1])
        tar_hash = sys.argv[2]
        log(f"==> provided_hash={tar_hash}")
    else:
        provider = Ebb.w3.toChecksumAddress(job.provider_addr)

    job.folders_to_share = job.paths
    check_link_folders(job.data_paths, job.registered_data_files, is_pass=is_pass)
    return submit(provider, requester, job, required_confs=required_confs)


if __name__ == "__main__":
    try:
        job = Job()
        fn = "job.yaml"
        job.set_config(fn)
        submit_eudat(job)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print_tb(str(e))
