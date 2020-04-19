#!/usr/bin/env python3

import sys
import traceback

from config import logging  # noqa: F401
from imports import connect
from lib import WHERE


def get_requester_info(requester):
    try:
        eBlocBroker, w3 = connect()
    except:
        raise

    try:
        requester = w3.toChecksumAddress(requester)
        if not eBlocBroker.functions.doesRequesterExist(requester).call():
            logging.error(
                f"E: Requester({requester}) is not registered.\n"
                "Please try again with registered Ethereum Address as requester. \n"
                "You can register your requester using: register_requester.py script"
            )
            raise

        blockReadFrom, orcid = eBlocBroker.functions.getRequesterInfo(requester).call()
        event_filter = eBlocBroker.events.LogRequester.createFilter(
            fromBlock=int(blockReadFrom), toBlock=int(blockReadFrom) + 1
        )
        requester_info = {
            "requester": requester,
            "blockReadFrom": blockReadFrom,
            "email": event_filter.get_all_entries()[0].args["email"],
            "miniLockID": event_filter.get_all_entries()[0].args["miniLockID"],
            "ipfsID": event_filter.get_all_entries()[0].args["ipfsID"],
            "fID": event_filter.get_all_entries()[0].args["fID"],
            "orcid": orcid.decode("utf-8"),
            "orcidVerify": eBlocBroker.functions.isOrcIDVerified(requester).call(),
        }
        return requester_info
    except Exception:
        logging.error(f"[{WHERE(1)}] - {traceback.format_exc()}")
        raise


if __name__ == "__main__":
    if len(sys.argv) == 1:
        requester = "0x57b60037b82154ec7149142c606ba024fbb0f991"
    elif len(sys.argv) == 2:
        requester = str(sys.argv[1])

    try:
        requester_info = get_requester_info(requester)
        print(
            "{0: <15}".format("requester: ")
            + requester_info["requester"]
            + "\n"
            + "{0: <15}".format("blockReadFrom: ")
            + str(requester_info["blockReadFrom"])
            + "\n"
            + "{0: <15}".format("email: ")
            + requester_info["email"]
            + "\n"
            + "{0: <15}".format("miniLockID: ")
            + requester_info["miniLockID"]
            + "\n"
            + "{0: <15}".format("ipfsID: ")
            + requester_info["ipfsID"]
            + "\n"
            + "{0: <15}".format("fID: ")
            + requester_info["fID"]
            + "\n"
            + "{0: <15}".format("orcid: ")
            + requester_info["orcid"]
            + "\n"
            + "{0: <15}".format("orcidVerify: ")
            + str(requester_info["orcidVerify"])
        )
    except Exception:
        sys.exit(1)
