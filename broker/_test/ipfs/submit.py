#!/usr/bin/env python3

from broker.ipfs.submit import submit_ipfs


def main():
    submit_ipfs("/home/alper/ebloc-broker/broker/_test/ipfs/job.yaml")


if __name__ == "__main__":
    main()
