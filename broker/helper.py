#!/usr/bin/env python3

import argparse


def helper():
    """Guide for argiments."""
    parser = argparse.ArgumentParser(
        description="""ebloc-broker""", epilog="""Run: nohup python3 -u ./Driver.py > cmd.log &!"""
    )
    parser.add_argument("--bn", type=int, default=0, help="Block number to start the test from")
    parser.add_argument("bar", nargs="*", default=[1, 2, 3], help="HELP")
    return parser.parse_args()
