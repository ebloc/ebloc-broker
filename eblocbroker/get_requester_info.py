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
            "address": requester,
            "block_read_from": blockReadFrom,
            "email": event_filter.get_all_entries()[0].args["email"],
            "gpg_fingerprint": event_filter.get_all_entries()[0].args["gpgFingerprint"].rstrip(b"\x00").hex(),
            "ipfs_id": event_filter.get_all_entries()[0].args["ipfsID"],
            "f_id": event_filter.get_all_entries()[0].args["fID"],
            "orcid": orcid.decode("utf-8"),
            "is_orcid_verified": self.eBlocBroker.functions.isOrcIDVerified(requester).call(),
        }
        return requester_info
    except Exception:
        _colorize_traceback()
        raise


if __name__ == "__main__":
    from eblocbroker.Contract import Contract

    contract = Contract()
    if len(sys.argv) == 1:
        requester = "0x12ba09353d5C8aF8Cb362d6FF1D782C1E195b571"
    elif len(sys.argv) == 2:
        requester = str(sys.argv[1])

    try:
        requester_info = contract.get_requester_info(requester)
        for key, value in requester_info.items():
            if key == "block_read_from":
                value = requester_info["block_read_from"]
            print("{0: <19}".format(f"{key}:") + str(value))
    except Exception:
        sys.exit(1)
