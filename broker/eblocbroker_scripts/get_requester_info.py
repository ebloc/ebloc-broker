#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils.tools import is_byte_str_zero, log, print_tb
from broker.errors import QuietExit


def get_requester_info(self, requester):
    """Return requester information."""
    try:
        requester = self.w3.toChecksumAddress(requester)
        if not self.does_requester_exist(requester):
            log(
                f"E: Requester({requester}) is not registered.\n"
                "Please try again with registered Ethereum Address as requester.\n"
                "You can register requester using: [blue]./broker/eblocbroker_scripts/register_requester.py",
            )
            raise QuietExit

        block_read_from, orc_id = self._get_requester_info(requester)
        event_filter = self._eblocbroker.events.LogRequester.createFilter(
            fromBlock=int(block_read_from), toBlock=int(block_read_from) + 1
        )
        gpg_fingerprint = event_filter.get_all_entries()[0].args["gpgFingerprint"].rstrip(b"\x00").hex()[24:].upper()
        requester_info = {
            "address": requester.lower(),
            "block_read_from": block_read_from,
            "gmail": event_filter.get_all_entries()[0].args["gmail"],
            "gpg_fingerprint": gpg_fingerprint,
            "ipfs_id": event_filter.get_all_entries()[0].args["ipfsID"],
            "f_id": event_filter.get_all_entries()[0].args["fID"],
            "is_orcid_verified": self.is_orcid_verified(requester),
        }
        if not is_byte_str_zero(orc_id):
            requester_info["orc_id"] = orc_id.decode("utf-8").replace("\x00", "")

        return requester_info
    except Exception as e:
        print_tb(e)
        raise e


if __name__ == "__main__":
    Ebb = cfg.Ebb
    if len(sys.argv) == 1:
        requester = "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49"
    elif len(sys.argv) == 2:
        requester = str(sys.argv[1])

    try:
        requester_info = Ebb.get_requester_info(requester)
        log(requester_info)
    except Exception as e:
        print_tb(e)
