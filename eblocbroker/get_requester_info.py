#!/usr/bin/env python3

import sys

from config import logging  # noqa: F401
from utils import _colorize_traceback, log


def get_requester_info(self, requester):
    try:
        requester = self.w3.toChecksumAddress(requester)

        if not self.does_requester_exist(requester):
            log(
                f"E: Requester({requester}) is not registered.\n"
                "Please try again with registered Ethereum Address as requester. \n"
                "You can register your requester using: register_requester.py script",
                "red",
            )
            raise

        blockReadFrom, orcid = self.eBlocBroker.functions.getRequesterInfo(requester).call()
        event_filter = self.eBlocBroker.events.LogRequester.createFilter(
            fromBlock=int(blockReadFrom), toBlock=int(blockReadFrom) + 1
        )
        requester_info = {
            "requester": requester,
            "blockReadFrom": blockReadFrom,
            "email": event_filter.get_all_entries()[0].args["email"],
            "gpgFingerprint": event_filter.get_all_entries()[0].args["gpgFingerprint"].rstrip(b"\x00").hex(),
            "ipfsID": event_filter.get_all_entries()[0].args["ipfsID"],
            "fID": event_filter.get_all_entries()[0].args["fID"],
            "orcid": orcid.decode("utf-8"),
            "orcidVerify": self.eBlocBroker.functions.isOrcIDVerified(requester).call(),
        }
        return requester_info
    except Exception:
        _colorize_traceback()
        raise


if __name__ == "__main__":
    from eblocbroker.Contract import Contract

    contract = Contract()

    if len(sys.argv) == 1:
        requester = "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49"
    elif len(sys.argv) == 2:
        requester = str(sys.argv[1])

    try:
        requester_info = contract.get_requester_info(requester)
        for key, value in requester_info.items():
            if key == "orcidVerify":
                value = requester_info["orcidVerify"]
            print("{0: <16}".format(f"{key}:") + str(value))
    except Exception:
        sys.exit(1)
