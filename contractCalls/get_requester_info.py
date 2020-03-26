#!/usr/bin/env python3

import sys
import traceback

from imports import connect


def get_requester_info(requester):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return

    requester = w3.toChecksumAddress(requester)
    if not eBlocBroker.functions.doesRequesterExist(requester).call():
        return (
            False,
            "Requester is not registered. Please try again with registered Ethereum Address as requester. \nYou can register your requester using: register_requester.py script.",
        )

    try:
        blockReadFrom, orcid = eBlocBroker.functions.getRequesterInfo(requester).call()
        event_filter = eBlocBroker.events.LogRequester.createFilter(fromBlock=int(blockReadFrom), toBlock=int(blockReadFrom) + 1)
        requesterInfo = {
            "requester": requester,
            "blockReadFrom": blockReadFrom,
            "email": event_filter.get_all_entries()[0].args["email"],
            "miniLockID": event_filter.get_all_entries()[0].args["miniLockID"],
            "ipfsID": event_filter.get_all_entries()[0].args["ipfsID"],
            "fID": event_filter.get_all_entries()[0].args["fID"],
            "orcid": orcid.decode("utf-8"),
            "orcidVerify": eBlocBroker.functions.isOrcIDVerified(requester).call(),
        }
        return True, requesterInfo
    except Exception:
        return False, traceback.format_exc()


if __name__ == "__main__":
    if len(sys.argv) == 3:
        requester = str(sys.argv[1])
        printType = str(sys.argv[2])
    elif len(sys.argv) == 2:
        requester = str(sys.argv[1])
        printType = "0"
    else:
        requester = "0x57b60037b82154ec7149142c606ba024fbb0f991"
        printType = "0"

    success, requesterInfo = get_requester_info(requester)

    if success:
        print(
            "{0: <15}".format("requester: ")
            + requesterInfo["requester"]
            + "\n"
            + "{0: <15}".format("blockReadFrom: ")
            + str(requesterInfo["blockReadFrom"])
            + "\n"
            + "{0: <15}".format("email: ")
            + requesterInfo["email"]
            + "\n"
            + "{0: <15}".format("miniLockID: ")
            + requesterInfo["miniLockID"]
            + "\n"
            + "{0: <15}".format("ipfsID: ")
            + requesterInfo["ipfsID"]
            + "\n"
            + "{0: <15}".format("fID: ")
            + requesterInfo["fID"]
            + "\n"
            + "{0: <15}".format("orcid: ")
            + requesterInfo["orcid"]
            + "\n"
            + "{0: <15}".format("orcidVerify: ")
            + str(requesterInfo["orcidVerify"])
        )
    else:
        print(requesterInfo)
