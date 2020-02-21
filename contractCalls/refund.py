#!/usr/bin/env python3

import pprint
import sys
import traceback
from os.path import expanduser

from imports import connect, connect_to_eblocbroker, connect_to_web3
from lib import PROVIDER_ID

home = expanduser("~")


def refund(provider, _from, key, index, jobID, sourceCodeHashArray):
    eBlocBroker, w3 = connect()
    provider = w3.toChecksumAddress(provider)
    _from = w3.toChecksumAddress(_from)

    if not eBlocBroker.functions.doesProviderExist(provider).call():
        return (False, f"E: Requested provider's Ethereum Address {provider} does not exist.")

    if provider != _from and not eBlocBroker.functions.doesRequesterExist(_from).call():
        return (False, f"E: Requested requester's Ethereum Address {_from} does not exist.")
    try:
        gasLimit = 4500000
        tx = eBlocBroker.functions.refund(provider, key, index, jobID, sourceCodeHashArray).transact(
            {"from": _from, "gas": gasLimit}
        )
    except Exception:
        return False, traceback.format_exc()

    return True, tx.hex()


if __name__ == "__main__":
    eBlocBroker, w3 = connect()

    if len(sys.argv) == 7:
        provider = w3.toChecksumAddress(str(sys.argv[1]))
        _from = w3.toChecksumAddress(str(sys.argv[2]))
        key = str(sys.argv[3])
        index = int(sys.argv[4])
        jobID = int(sys.argv[5])
        sourceCodeHashArray = sys.argv[6]
    else:
        provider = w3.toChecksumAddress(PROVIDER_ID)
        _from = w3.toChecksumAddress(PROVIDER_ID)
        key = "QmXFVGtxUBLfR2cYPNQtUjRxMv93yzUdej6kYwV1fqUD3U"
        index = 0
        jobID = 0
        sourceCodeHashArray = [
            b'\x93\xa52\x1f\x93\xad\\\x9d\x83\xb5,\xcc\xcb\xba\xa59~\xc3\x11\xe6%\xd3\x8d\xfc+"\x185\x03\x90j\xd4'
        ]  # should pull from the event

    status, tx_hash = refund(provider, _from, key, index, jobID, sourceCodeHashArray)
    if not status:
        print(tx_hash)
        sys.exit()
    else:
        print("tx_hash=" + tx_hash)
        receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        print("Transaction receipt mined: \n")
        pprint.pprint(dict(receipt))
        print("Was transaction successful?")
        pprint.pprint(receipt["status"])
        if receipt["status"] == 1:
            logs = eBlocBroker.events.LogJob().processReceipt(receipt)
            try:
                print("Job's index=" + str(logs[0].args["index"]))
            except IndexError:
                print("Transaction is reverted.")
