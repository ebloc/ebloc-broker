#!/usr/bin/env python3

import sys
from pprint import pprint
from typing import List

from web3.logs import DISCARD

from config import env, logging  # noqa: F401
from lib import get_tx_status
from utils import _colorize_traceback, log


def refund(self, provider, _from, job_key, index, job_id, cores, elapsed_time):
    provider = self.w3.toChecksumAddress(provider)
    _from = self.w3.toChecksumAddress(_from)

    if not self.eBlocBroker.functions.doesProviderExist(provider).call():
        logging.error(f"E: Requested provider's Ethereum address {provider} does not exist")
        raise

    if provider != _from and not self.eBlocBroker.functions.doesRequesterExist(_from).call():
        logging.error(f"E: Requested requester's Ethereum address {_from} does not exist")
        raise

    try:
        gas_limit = 4500000
        tx = self.eBlocBroker.functions.refund(provider, job_key, index, job_id, cores, elapsed_time).transact(
            {"from": _from, "gas": gas_limit}
        )
        return tx.hex()
    except Exception:
        _colorize_traceback()
        raise


if __name__ == "__main__":
    import eblocbroker.Contract as Contract

    Ebb = Contract.eblocbroker

    if len(sys.argv) == 7:
        provider = Ebb.w3.toChecksumAddress(str(sys.argv[1]))
        _from = Ebb.w3.toChecksumAddress(str(sys.argv[2]))
        job_key = str(sys.argv[3])
        index = int(sys.argv[4])
        job_id = int(sys.argv[5])
        cores = sys.argv[6]  # type: List[str]
        elapsed_time = sys.argv[7]  # type: List[str]
    else:
        provider = Ebb.w3.toChecksumAddress(env.PROVIDER_ID)
        _from = Ebb.w3.toChecksumAddress(env.PROVIDER_ID)
        job_key = "QmXFVGtxUBLfR2cYPNQtUjRxMv93yzUdej6kYwV1fqUD3U"
        index = 0
        job_id = 0
        cores = ["1"]
        elapsed_time = ["5"]

    try:
        tx_hash = Ebb.refund(provider, _from, job_key, index, job_id, cores, elapsed_time)
        receipt = get_tx_status(tx_hash)
        if receipt["status"] == 1:
            processed_logs = Ebb.eBlocBroker.events.LogRefundRequest().processReceipt(receipt, errors=DISCARD)
            pprint(vars(processed_logs[0].args))
            try:
                logging.info(f"refunded_wei={processed_logs[0].args['refundedWei']}")
                log("SUCCESS", "green")
            except Exception:
                logging.error("E: Transaction is reverted")
    except Exception as e:
        if type(e).__name__ != "QuietExit":
            _colorize_traceback()
        sys.exit(1)
