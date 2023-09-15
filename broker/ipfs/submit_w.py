#!/usr/bin/env python3

import os
from pathlib import Path
from sys import platform
from broker._utils.yaml import Yaml
from broker import cfg
from broker._utils.tools import log
from broker.config import env
from broker.eblocbroker_scripts.job import Job
from broker.errors import QuietExit
from broker.lib import run
from broker.link import check_link_folders
from broker.utils import (
    StorageID,
    generate_md5sum,
    ipfs_to_bytes32,
    is_bin_installed,
    is_dpkg_installed,
    print_tb,
    start_ipfs_daemon,
)

# TODO: folders_to_share let user directly provide the IPFS hash instead of the folder
Ebb = cfg.Ebb
ipfs = cfg.ipfs


cfg.TEST_PROVIDERS = [
    "0x29e613B04125c16db3f3613563bFdd0BA24Cb629",  # leo
    "0x4934a70Ba8c1C3aCFA72E809118BDd9048563A24",  # leo1
    "0xe2e146d6B456760150d78819af7d276a1223A6d4",  # leo2
]


def pre_check_gpg(requester):
    requester_info = Ebb.get_requester_info(requester)
    from_gpg_fingerprint = ipfs.get_gpg_fingerprint(env.GMAIL).upper()
    if requester_info["gpg_fingerprint"].upper() != from_gpg_fingerprint:
        raise Exception(
            f"requester({requester})'s gpg_fingerprint({requester_info['gpg_fingerprint'].upper()}) does not "
            f"match with registered gpg_fingerprint={from_gpg_fingerprint}"
        )

    try:
        ipfs.is_gpg_published(from_gpg_fingerprint)
    except Exception as e:
        raise e


def pre_check(job: Job, requester):
    """Pre check jobs to submit."""
    for storage_id in job.storage_ids:
        if storage_id == StorageID.IPFS_GPG:
            pre_check_gpg(requester)
            break

    job.check_account_status(requester)
    is_bin_installed("ipfs")
    if platform == "linux" or platform == "linux2":
        if not is_dpkg_installed("pigz"):
            raise Exception("Install pigz.\nsudo apt install -y pigz")
    elif platform == "darwin":
        try:
            is_bin_installed("pigz")
        except Exception:
            raise Exception("Install pigz.\nbrew install pigz")

    if not os.path.isfile(env.GPG_PASS_FILE):
        log(f"E: Please store your gpg password in the [m]{env.GPG_PASS_FILE}[/m] file for decryption", is_wrap=True)
        raise QuietExit

    start_ipfs_daemon()
    if job.storage_ids[0] == StorageID.IPFS:
        for storage_id in job.storage_ids[1:]:
            if storage_id in (StorageID.GDRIVE, StorageID.B2DROP):
                raise Exception(
                    "If source-code is submitted via IPFS, then the data must be submitted using IPFS or IPFS_GPG"
                )


def _ipfs_add(job, target, idx, is_verbose=False):
    try:
        ipfs_hash = ipfs.add(target)
        # ipfs_hash = ipfs.add(folder, True)  # True includes .git/
        run(["ipfs", "refs", ipfs_hash])
    except Exception as e:
        print_tb(e)
        raise e

    if idx == 0:
        job.key = ipfs_hash

    job.code_hashes.append(ipfs_to_bytes32(ipfs_hash))
    job.code_hashes_str.append(ipfs_hash)
    if is_verbose:
        log(f"==> ipfs_hash={ipfs_hash} | md5sum={generate_md5sum(target)}")

    return job


#: heft
def submit_ipfs_calc(job: Job, is_pass=False, is_verbose=True):
    if is_verbose:
        log(f"==> attemptting to submit job ({job.source_code_path}) using [g]IPFS[/g]")

    requester = Ebb.w3.toChecksumAddress(job.requester_addr)
    Ebb._pre_check(requester)
    try:
        pre_check(job, requester)
    except Exception as e:
        raise e

    main_storage_id = job.storage_ids[0]
    job.folders_to_share = job.paths
    check_link_folders(job.data_paths, job.registered_data_files, job.source_code_path, is_pass=is_pass)
    if main_storage_id == StorageID.IPFS:
        if is_verbose:
            log("==> submitting source code through [blue]IPFS[/blue]")
    elif main_storage_id == StorageID.IPFS_GPG:
        if is_verbose:
            log("==> submitting source code through [blue]IPFS_GPG[/blue]")
    else:
        raise Exception("Please provide IPFS or IPFS_GPG storage type for the source code")

    # provider_info = Ebb.get_provider_info(job.provider_addr)
    targets = []
    is_ipfs_gpg = False
    for idx, folder in enumerate(job.folders_to_share):
        if isinstance(folder, Path):
            target = folder
            if job.storage_ids[idx] == StorageID.IPFS_GPG:
                is_ipfs_gpg = True
                job.code_hashes.append(b"")  # dummy items added
                job.code_hashes_str.append("")  # dummy items added
            else:
                if idx == 0 and job.input_files:
                    breakpoint()  # DEBUG

                job = _ipfs_add(job, target, idx, is_verbose)
        else:
            code_hash = folder
            if isinstance(code_hash, bytes):
                job.code_hashes.append(code_hash)
                job.code_hashes_str.append(code_hash.decode("utf-8"))

    provider_addr = job.search_best_provider(requester, is_verbose=is_verbose)


def main():
    yaml_fn = Path.home() / "ebloc-broker" / "broker" / "ipfs" / "job_workflow.yaml"
    yaml_original = Yaml(yaml_fn)
    BASE = Path.home() / "test_eblocbroker" / "test_data" / "base" / "source_code_wf_random"
    yaml_fn_jobs = BASE / "jobs.yaml"
    yaml_jobs = Yaml(yaml_fn_jobs)
    for _job in yaml_jobs["config"]["jobs"]:
        job = Job()
        my_job = yaml_jobs["config"]["jobs"][_job]
        #
        yaml_original["config"]["dt_in"] = my_job["dt_in"]
        yaml_original["config"]["data_transfer_out"] = my_job["dt_out"]
        yaml_original["config"]["jobs"]["job1"]["run_time"] = my_job["run_time"]
        job.set_config(yaml_fn)
        submit_ipfs_calc(job)
        my_job["costs"] = {}
        #: fetch calcualted cost
        yaml_original = Yaml(yaml_fn)
        for address in yaml_original["config"]["costs"]:
            my_job["costs"][address] = yaml_original["config"]["costs"][address]


if __name__ == "__main__":
    try:
        main()
    except QuietExit as e:
        log(f"==> {e}")
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print_tb(e)
