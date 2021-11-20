#!/usr/bin/env python3

from broker.eblocbroker.job import Job
from broker.eudat.submit import eudat_submit
from broker.gdrive.submit import submit_gdrive
from broker.ipfs.submit import submit_ipfs


class SubmitBase:
    def __init__(self):
        self.job = Job()
        self.job.set_config("/home/alper/ebloc-broker/broker/ipfs/job.yaml")
        self.submit()

    def submit(self):
        if self.job.source_code_storage_id in ["ipfs", "ipfs_gpg"]:
            submit_ipfs(self.job)
        elif self.job.source_code_storage_id == "eudat":
            eudat_submit(self.job)
        elif self.job.source_code_storage_id == "gdrive":
            submit_gdrive(self.job)


def main():
    SubmitBase()


if __name__ == "__main__":
    main()
