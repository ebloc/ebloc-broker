#!/usr/bin/env python3

import sys

import broker.cfg as cfg
from broker._utils.tools import log, print_tb


def get_requester_info(self, requester):
    """Return requester information."""
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

        block_read_from, orcid = self._get_requester_info(requester)
        event_filter = self._eBlocBroker.events.LogRequester.createFilter(
            fromBlock=int(block_read_from), toBlock=int(block_read_from) + 1
        )
        requester_info = {
            "address": requester,
            "block_read_from": block_read_from,
            "email": event_filter.get_all_entries()[0].args["email"],
            "gpg_fingerprint": event_filter.get_all_entries()[0].args["gpgFingerprint"].rstrip(b"\x00").hex(),
            "ipfs_id": event_filter.get_all_entries()[0].args["ipfsID"],
            "f_id": event_filter.get_all_entries()[0].args["fID"],
            "orcid": orcid.decode("utf-8"),
            "is_orcid_verified": self.is_orcid_verified(requester),
        }
        return requester_info
    except Exception as e:
        print_tb(e)
        raise e


if __name__ == "__main__":
    Ebb = cfg.Ebb
    if len(sys.argv) == 1:
        requester = "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49"
        # requester = "0x12ba09353d5C8aF8Cb362d6FF1D782C1E195b571"
    elif len(sys.argv) == 2:
        requester = str(sys.argv[1])

    try:
        requester_info = Ebb.get_requester_info(requester)
        for key, value in requester_info.items():
            if key == "block_read_from":
                value = requester_info["block_read_from"]
            print("{0: <19}".format(f"{key}:") + str(value))
    except Exception as e:
        print_tb(e)
