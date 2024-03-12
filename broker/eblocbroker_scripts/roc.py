#!/usr/bin/env python3

import networkx as nx

from broker import cfg, config
from broker._utils._log import log
from broker.config import env, setup_logger
from broker.utils import print_tb

Ebb = cfg.Ebb
logging = setup_logger()

G = nx.Graph()


# G.add_edge("2", "1.1")

"""
"""


def roc_log():
    output = Ebb.get_block_number()
    event_filter = config.auto.events.LogSoftwareExecRecord.createFilter(
        # argument_filters={"to": str(provider)},
        fromBlock=23066710,
        toBlock="latest",
    )
    for logged_receipt in event_filter.get_all_entries():
        log(logged_receipt.args)
        sw = logged_receipt.args.sourceCodeHash
        sw = sw.hex()[32:64]
        token_index = config.roc.getTokenIndex(sw)
        index = logged_receipt.args.index
        sw_str = f"{token_index}.{index}"
        #
        input_hash_bytes = logged_receipt.args.inputHash
        output_hash_bytes = logged_receipt.args.outputHash

        input_hash_token_index = []
        for inp in input_hash_bytes:
            _hash = inp.hex()[32:64]
            input_hash_token_index.append(config.roc.getTokenIndex(_hash))

        output_hash_token_index = []
        for out in output_hash_bytes:
            _hash = out.hex()[32:64]
            output_hash_token_index.append(config.roc.getTokenIndex(_hash))

        for inp in input_hash_token_index:
            G.add_edge(inp, sw_str)

        for out in output_hash_token_index:
            G.add_edge(sw_str, out)

    nx.nx_pydot.write_dot(G, "original_from_bloxberg.gv")


def roc():
    output = Ebb.get_block_number()
    provider = "0x29e613B04125c16db3f3613563bFdd0BA24Cb629"
    event_filter = config._roc.events.Transfer.createFilter(
        argument_filters={"to": str(provider)},
        fromBlock=23066710,
        toBlock="latest",
    )
    for logged_receipt in event_filter.get_all_entries():
        log(logged_receipt.args)
        token_id = logged_receipt.args["tokenId"]


def main():
    # roc()
    roc_log()


if __name__ == "__main__":
    main()
