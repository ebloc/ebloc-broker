#!/usr/bin/env python3

import sys

import dill as pickle

from broker.config import env
from brownie import project

is_load = False

if not is_load:
    from brownie import network

    network.connect("bloxberg")
    project = project.load(env.CONTRACT_PROJECT_PATH)
    ebb = project.eBlocBroker.at("0xccD25f5Ae21037a6DCCff829B01034E2fD332796")
else:
    sys.setrecursionlimit(10_000)
    try:
        ebb = pickle.loads(open(".network.pk", mode="rb"))
    except:
        from brownie import network

        network.connect("bloxberg")
        project = project.load(env.CONTRACT_PROJECT_PATH)
        ebb = project.eBlocBroker.at("0xccD25f5Ae21037a6DCCff829B01034E2fD332796")
        pickle.save(ebb, ".network.pk")

print(ebb.getOwner())


gpg_fingerprint = "420E5F7E1928B5E5940FA8D44055CB84FC8DCE5F"
email = "alper.alimoglu.research@gmail.com"
federation_cloud_id = "5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu"
ipfs_id = "/ip4/85.96.79.178/tcp/4001/p2p/12D3KooW9s3zzzafmoZ79dRLX3TBFGYHiADPDtxoo4SeiN8B1qGd"  # TODO: delete
ops = {"from": "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49", "gas": 4500000}
tx = ebb.updateProviderInfo(gpg_fingerprint, email, federation_cloud_id, ipfs_id, ops)


# home = expanduser("~")
# BASE = f"{home}/ebloc-broker/broker/eblocbroker"
# abi_file = f"{BASE}/abi.json"
# contract_file = f"{BASE}/contract.json"
# _file = open(abi_file, "w")
# json.dump(ebb.abi, _file)


# >>> accounts.load("alpy.json", "alper")
# <LocalAccount '0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49'>
