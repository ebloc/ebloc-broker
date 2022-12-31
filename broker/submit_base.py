#!/usr/bin/env python3

from pathlib import Path

from broker.eblocbroker_scripts.job import Job
from broker.eudat.submit import submit_b2drop
from broker.gdrive.submit import submit_gdrive
from broker.ipfs.submit import submit_ipfs


class SubmitBase:
    def __init__(self, yaml_fn):
        self.job = Job()
        self.job.set_config(yaml_fn)

    def submit(self, is_pass=False, required_confs=1):
        if self.job.source_code_storage_id in ["ipfs", "ipfs_gpg"]:
            return submit_ipfs(self.job, is_pass, required_confs)
        elif self.job.source_code_storage_id == "b2drop":
            return submit_b2drop(self.job, is_pass, required_confs)
        elif self.job.source_code_storage_id == "gdrive":
            return submit_gdrive(self.job, is_pass, required_confs)

        raise Exception("source_code_storage_id is not valid")


def main():
    SubmitBase(Path.home() / "ebloc-broker" / "broker" / "ipfs" / "job.yaml")


if __name__ == "__main__":
    main()
