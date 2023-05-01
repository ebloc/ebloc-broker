#!/usr/bin/env python3

import os
import psutil
import time

from broker._utils._log import br, log
from broker.config import env


def print_msg(msg):
    string = f"{time.ctime()},pid={os.getpid()}"
    log(f"{br(string)} {msg}")


def test():
    from brownie import network, project

    print_msg(f"parent pid: {psutil.Process().parent().pid}, start calculate()")
    network.connect("bloxberg")
    project = project.load(env.CONTRACT_PROJECT_PATH)
    ebb = project.eBlocBroker.at("0xccD25f5Ae21037a6DCCff829B01034E2fD332796")
    print(ebb.getOwner())
    print_msg(f"parent pid: {psutil.Process().parent().pid}, end calculate()")


def calculate(func_name, *args):
    from brownie import network, project

    print_msg(f"parent pid: {psutil.Process().parent().pid}, start calculate()")
    print(f"func_name={func_name} | {args}")
    network.connect("bloxberg")
    project = project.load(env.CONTRACT_PROJECT_PATH)
    ebb = project.eBlocBroker.at("0xccD25f5Ae21037a6DCCff829B01034E2fD332796")
    print(ebb.getOwner())
    print_msg(f"parent pid: {psutil.Process().parent().pid}, end calculate()")


if __name__ == "__main__":
    test()
    # func_name = sys.argv[1]
    # if len(sys.argv) > 1:
    #     calculate(func_name, *sys.argv[2:])
