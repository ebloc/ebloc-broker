#!/usr/bin/python3

from brownie import *

def main():
    accounts[0].deploy(Lib)
    eBlocBrokerAddress = accounts[0].deploy(eBlocBroker)
