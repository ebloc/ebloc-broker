#!/usr/bin/env python3

from shutil import copyfile

from broker.config import env
from broker.ipfs.submit import submit_ipfs


def main():
    job_yaml = env.HOME / "ebloc-broker" / "broker" / "_test" / "ipfs" / "job.yaml"
    job_yaml_temp = job_yaml.replace(".yaml", "_temp.yaml")
    copyfile(job_yaml, job_yaml_temp)

    submit_ipfs(job_yaml_temp)


if __name__ == "__main__":
    main()
