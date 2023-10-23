#!/usr/bin/env python3

from broker._utils._log import log
import sys

from broker import cfg, config
from broker._utils.tools import log
from broker.config import env, setup_logger
from broker.utils import print_tb

Ebb = cfg.Ebb
logging = setup_logger()
cfg.NETWORK_ID = "bloxberg"


def roc():
    output = Ebb.get_block_number()
    # print(output)

    provider = "0x29e613B04125c16db3f3613563bFdd0BA24Cb629"
    event_filter = config._roc.events.Transfer.createFilter(
        argument_filters={"to": str(provider)},
        fromBlock=22532314,
        toBlock="latest",
    )
    for logged_receipt in event_filter.get_all_entries():
        log(logged_receipt.args)
        token_id = logged_receipt.args["tokenId"]

    breakpoint()  # DEBUG


def main():
    roc()


if __name__ == "__main__":
    main()
