#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils._log import log
from broker.config import env
from broker.eblocbroker_scripts.job import Job
from broker.errors import QuietExit
from broker.imports import connect
from broker.libs.eudat import login, submit
from broker.link import check_link_folders
from broker.utils import print_tb


def submit_b2drop(job: Job, is_pass=False, required_confs=1):
    log("==> Submitting source code through [blue]B2DROP[/blue]")
    Ebb = cfg.Ebb
    requester = Ebb.w3.toChecksumAddress(job.requester_addr)
    Ebb._pre_check(requester)
    oc_client = env.OC_USER
    connect()
    try:
        job.check_account_status(requester)
    except Exception as e:
        print_tb(e)
        raise e

    login(oc_client, env.LOG_DIR.joinpath(".b2drop_client.txt"), env.OC_CLIENT)
    provider = Ebb.w3.toChecksumAddress(job.provider_addr)
    job.folders_to_share = job.paths
    check_link_folders(job.data_paths, job.registered_data_files, job.source_code_path, is_pass=is_pass)
    return submit(provider, requester, job, required_confs=required_confs)


if __name__ == "__main__":
    try:
        job = Job()
        fn = "job.yaml"
        job.set_config(fn)
        submit_b2drop(job)
    except KeyboardInterrupt:
        sys.exit(1)
    except QuietExit as e:
        log(f"==> {e}")
    except Exception as e:
        print_tb(str(e))
