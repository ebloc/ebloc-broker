#!/usr/bin/env python3

import sys
import traceback

from config import env, logging  # noqa: F401
from imports import connect
from lib import WHERE, get_tx_status


def refund(provider, _from, job_key, index, job_id, source_code_hashes):
    eBlocBroker, w3 = connect()
    provider = w3.toChecksumAddress(provider)
    _from = w3.toChecksumAddress(_from)

    if not eBlocBroker.functions.doesProviderExist(provider).call():
        logging.error(f"E: Requested provider's Ethereum address {provider} does not exist")
        raise

    if provider != _from and not eBlocBroker.functions.doesRequesterExist(_from).call():
        logging.error(f"E: Requested requester's Ethereum address {_from} does not exist")
        raise

    try:
        gas_limit = 4500000
        tx = eBlocBroker.functions.refund(provider, job_key, index, job_id, source_code_hashes).transact(
            {"from": _from, "gas": gas_limit}
        )
        return tx.hex()
    except Exception:
        logging.error(f"[{WHERE(1)}] - {traceback.format_exc()}")
        raise


if __name__ == "__main__":
    eBlocBroker, w3 = connect()
    if len(sys.argv) == 7:
        provider = w3.toChecksumAddress(str(sys.argv[1]))
        _from = w3.toChecksumAddress(str(sys.argv[2]))
        job_key = str(sys.argv[3])
        index = int(sys.argv[4])
        job_id = int(sys.argv[5])
        source_code_hashes = sys.argv[6]
    else:
        provider = w3.toChecksumAddress(env.PROVIDER_ID)
        _from = w3.toChecksumAddress(env.PROVIDER_ID)
        job_key = "QmXFVGtxUBLfR2cYPNQtUjRxMv93yzUdej6kYwV1fqUD3U"
        index = 0
        job_id = 0
        # TODO:  pull from the event
        source_code_hashes = [
            b'\x93\xa52\x1f\x93\xad\\\x9d\x83\xb5,\xcc\xcb\xba\xa59~\xc3\x11\xe6%\xd3\x8d\xfc+"\x185\x03\x90j\xd4'
        ]

    try:
        tx_hash = refund(provider, _from, job_key, index, job_id, source_code_hashes)
        receipt = get_tx_status(tx_hash)
        if receipt["status"] == 1:
            logs = eBlocBroker.events.LogJob().processReceipt(receipt)
            try:
                logging.info(f"Job's index={logs[0].args['index']}")
            except Exception:
                logging.error("E: Transaction is reverted")
    except:
        logging.error(traceback.format_exc())
        sys.exit(1)
