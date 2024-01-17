#!/usr/bin/env python3

import random

from broker import cfg, config
from broker._utils._log import log
from broker._utils.tools import print_tb
from broker.config import env
from broker.errors import QuietExit
import networkx as nx
from typing import List

fn = "/home/alper/git/AutonomousSoftwareOrg/graph/original.gv"
G = nx.drawing.nx_pydot.read_dot(fn)

"""
Ebb = cfg.Ebb
Ebb.get_block_number()
"""

data_map = {
    "17.2": "9ea971a966ec0f612b268d7e089b1f9e",
    "10.0": "110e00c9266bf7cb964cd68f5e0a6b96",
    "7.0": "3930b695da4c9f46aa0ef0153d8ca288",
    "7.1": "8d7506d81cf589cc7603093272b68bef",
    "7.2": "b04e7dd0ef6ecd43eb3973b0d6952733",
    "7.3": "7080d03c288977b88812b865b761bffa",
    "7.4": "84f310b307a08955e01d9c2347adf77e",
    "17.1": "0f2290337f9cc909e62e4375a0353d7d",
    "17.4": "059dc553c65d19c917e94291016b6714",
    "14.0": "468e6561b82c811bb3c2324e2ca0865f",
    "14.1": "0e975e19d841b2d5e7facc93eaf3db2e",
    "4.0": "c69dc79f17e20e4ba5014f56492cddaf",
    "4.1": "c2fee597bc585140bb2f214c6f19d89e",
    "17.3": "42742ab7bfc995a7fc3490e663705590",
    "17.0": "5a259600f0c0a7984f380cd00b89d1fe",
    "22.3": "feb2c4b74f898c2064707843e0585fbe",
    "19.0": "be293b48fa60443023e308bea4ec4df8",
    "22.0": "a7e8fe2dcfeb2f4ddce864682133b60e",
    "22.1": "a715e0a320e144335bb0974acdbe3847",
    "22.2": "be038e12f93a275eb013192ab896c8a2",
    "1": "7dca945940426af6fb934a8ffb78cc8d",
    "2": "44f8657617b4d88473d19c3265b8aaa3",
    "3": "6e006040b06789a03549d4d383ad7d12",
    "4": "d547c04c3be46fd1d21a49971909ff01",
    "5": "e4151eb95ebee59a5a097c2cd4ce54e5",
    "6": "7654f412d3f776b99f63802a64c1b824",
    "7": "bd6680cd60dc68aba2aadee5693ae92a",
    "8": "7bddb12a66e4f9fd0e43412cdc2b2f32",
    "9": "dd230a453a7414fd47e0150d5f527bf0",
    "10": "188028ab4bf0b792321b4fc9c02cf923",
    "11": "588bef79b9a7fa2634aebae3f9905a9c",
    "12": "2173c32a5d7f0a65419f5a4dc3a99a58",
    "13": "e2973d46dfff661d6e8b9c25b21458a6",
    "14": "58f02953629a9889d5f6750c3781510f",
    "15": "94a30954fed4a365a321157161d8b9f3",
    "16": "81a97cd12cd7b20c2ca5f3d9c36ff7ae",
    "17": "ccaab53df3529738055a17c9e7cc7d41",
    "18": "a0a626242563cf2352ad257931c8609b",
    "19": "7468cffde8f1577bc0f33507e4090e49",
    "20": "79d6c3d678fbcdd536fbee848587048c",
    "21": "e7790d058d5f7cc261caff81e52ac32d",
    "22": "768e6bea2ef05c9b5edf3c0d77d21e7c",
    "23": "15e49f7bbfca87028895fa3ae467213b",
    "24": "9ea0867a32eb943f73ca0342a1200c25",
    "25": "6aa49ee32715265d478726ec2a35cdac",
    "26": "7e3f768ea26d8d26078dcb6a47e1641f",
    "27": "9eb75f65be7eeb9555042dbfb80af2ef",
    "28": "324b669cda201f4af6864c0fed7cdfca",
    "29": "20accb4b8302330af25bb1d50a871711",
    "30": "4292b88a00d24dc5993f7566787c3b79",
    "31": "39449643a82d5ec8e2cc53c9a60939a2",
    "32": "d3497227b36823d9ced2055b491efa7d",
    "33": "2a61b09dfc6a1d06cfedd32b4adb7255",
    "34": "77f3fb8ea03de6928a0c3e0ea3161315",
    "35": "887718ff634aa6d8d307ec12b41c4fe0",
    "36": "4d8b3e9f884d5985e7a4a6f785cce9f6",
    "37": "40b78751675f3008b1a08ca49b136cba",
    "38": "fd6a054d326f48f9d30c48b55f94e223",
    "39": "7936a659b2ed0c886e19c73ed6e66735",
    "40": "56227c20de5f6dcd9af579c9e675a940",
    "41": "7767eac039456e138af47679395feebc",
    "42": "b40e9030da0f3b8c958e3529708fdc50",
    "43": "6e858df716602f3d82feebd2ee7f52fe",
    "44": "6cb0a74562ecbddf25320212cc39df8e",
    "45": "f5be3dbd455a4aaeb21cb3d066991404",
    "46": "7be43e2eac44ed7225be3c932953bbbf",
    "47": "ed73e2bad0cd71150faa28ea015448c1",
    "48": "280b81a83943e753a2c5553cc3a127f4",
    "49": "47de855b72114be6dcad7564e48cd936",
}

orphan_data = ["1", "2", "11", "3", "44"]
generated_data: List[str] = []
completed_sw = []


def add_software_exec_record(sw, index, input_hashes, output_hashes):
    fn = env.PROVIDER_ID.lower().replace("0x", "") + ".json"
    Ebb.brownie_load_account(fn)

    if config.roc.getTokenIndex(sw) > 0:
        log(f"=> sw({sw}) is already created")
    else:
        log(f"=> [blue]sw({sw}) to be registered")
        config.auto.addSoftwareExecRecord(
            sw, index, input_hashes, output_hashes, {"from": env.PROVIDER_ID, "gas": 9900000, "allow_revert": True}
        )


def commit_software():
    while True:
        if len(completed_sw) == len(sw_nodes):
            break

        for sw_node in sw_nodes:
            if sw_node not in completed_sw:
                pre = set(G.predecessors(sw_node))
                if pre.issubset(orphan_data + generated_data):
                    input_hashes = []
                    for data in pre:
                        input_hashes.append(data_map[data])

                    output_hashes = []
                    succ = set(G.successors(sw_node))
                    for data in succ:
                        output_hashes.append(data_map[data])
                        generated_data.append(data)

                    completed_sw.append(sw_node)

                    #: save to blockchain
                    add_software_exec_record(data_map[sw_node], int(sw_node.split(".")[1]), input_hashes, output_hashes)


sw_nodes = []
for node in list(G.nodes):
    if "." in node:
        sw_nodes.append(node)

# commit_software()
"""
order = {}
for sw_node in sw_nodes:
    roc_num = config.roc.getTokenIndex(data_map[sw_node])
    order[sw_node] = roc_num

sorted_order = {k: v for k, v in sorted(order.items(), key=lambda item: item[1])}
log(sorted_order)
"""

sorted_order = {
    "10.0": 13,
    "17.2": 14,
    "7.2": 19,
    "7.3": 21,
    "7.4": 23,
    "14.0": 26,
    "4.0": 29,
    "4.1": 33,
    "7.1": 35,
    "14.1": 38,
    "17.0": 42,
    "17.3": 45,
    "19.0": 46,
    "17.4": 48,
    "22.3": 50,
    "7.0": 53,
    "17.1": 57,
    "22.0": 60,
    "22.1": 64,
    "22.2": 66,
}

hit_data = {}

for node in sorted_order:
    successors = set(G.successors(node))
    owned_data = []
    for succ in successors:
        if succ not in hit_data:
            owned_data.append(succ)
            hit_data[succ] = True

    log(f"{node} => {owned_data}")
    # breakpoint()  # DEBUG


#  set(G.predecessors("17.2"))
breakpoint()  # DEBUG


def md5_hash():
    _hash = random.getrandbits(128)
    return "%032x" % _hash


def commit_hash(_hash):
    roc_num = config.roc.getTokenIndex(_hash)
    if roc_num == 0:
        fn = env.PROVIDER_ID.lower().replace("0x", "") + ".json"
        Ebb.brownie_load_account(fn)
        config.roc.createCertificate(env.PROVIDER_ID, _hash, {"from": env.PROVIDER_ID})
    else:
        log(f"Nothing to do... {_hash} => {roc_num}")


def main():
    log(config.roc.name())
    log(config.auto.getAutonomousSoftwareOrgInfo())
    #
    commit_hash("50c4860efe8f597e39a2305b05b0c291")

    log(md5_hash())
    # output = md5_hash()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"#> {e}")
    except Exception as e:
        print_tb(str(e))
