#!/usr/bin/env python3

import argparse

from broker.helper import helper

args = helper()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--argument", type=str)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()
    from broker.Driver import main

    main()
