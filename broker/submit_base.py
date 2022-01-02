#!/usr/bin/env python3

from pathlib import Path

from broker.eblocbroker_scripts.job import Job
from broker.eudat.submit import eudat_submit
from broker.gdrive.submit import submit_gdrive
from broker.ipfs.submit import submit_ipfs


class SubmitBase:
    def __init__(self, yaml_fn):
        self.job = Job()
        self.job.set_config(yaml_fn)
        # self.submit()

    def submit(self, is_pass=False, required_confs=1):
        if self.job.source_code_storage_id in ["ipfs", "ipfs_gpg"]:
            return submit_ipfs(self.job, is_pass, required_confs)
        elif self.job.source_code_storage_id == "eudat":
            return eudat_submit(self.job, is_pass, required_confs)
        elif self.job.source_code_storage_id == "gdrive":
            return submit_gdrive(self.job, is_pass, required_confs)


def main():
    yaml_fn = Path.home() / "ebloc-broker" / "broker" / "ipfs" / "job.yaml"
    SubmitBase(yaml_fn)


if __name__ == "__main__":
    main()
