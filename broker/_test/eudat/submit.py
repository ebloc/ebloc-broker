#!/usr/bin/env python3

from broker.config import env
from broker.eudat.submit import submit_eudat


def main():
    job_yaml = env.HOME / "ebloc-broker" / "broker" / "_test" / "eudat" / "job.yaml"
    # job_yaml_temp = job_yaml.replace(".yaml", "_temp.yaml")
    # copyfile(job_yaml, job_yaml_temp)

    submit_eudat(job_yaml)


if __name__ == "__main__":
    main()
