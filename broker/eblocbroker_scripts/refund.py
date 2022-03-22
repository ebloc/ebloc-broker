#!/usr/bin/env python3

import sys
from typing import List
from web3.logs import DISCARD

from broker import cfg
from broker._utils._log import log
from broker._utils.tools import print_tb
from broker._utils.web3_tools import get_tx_status
from broker.config import env, logging  # noqa: F401
from broker.errors import QuietExit


def refund(self, provider, _from, job_key, index, job_id, cores, elapsed_time):
    """Refund job payment."""
    provider = self.w3.toChecksumAddress(provider)
    _from = self.w3.toChecksumAddress(_from)

    if not self.does_provider_exist(provider):
        raise Exception(f"Requested provider's Ethereum address {provider} does not exist")

    if provider != _from and not self.does_requester_exist(_from):
        raise Exception(f"Requested requester's Ethereum address {_from} does not exist")

    try:
        tx = self._refund(provider, job_key, index, job_id, cores, elapsed_time)
        return self.tx_id(tx)
    except Exception as e:
        print_tb(e)
        raise e


if __name__ == "__main__":
    Ebb = cfg.Ebb
    if len(sys.argv) == 7:
        provider = Ebb.w3.toChecksumAddress(str(sys.argv[1]))
        _from = Ebb.w3.toChecksumAddress(str(sys.argv[2]))
        job_key = str(sys.argv[3])
        index = int(sys.argv[4])
        job_id = int(sys.argv[5])
        cores = sys.argv[6]  # type: List[str]  # noqa
        elapsed_time = sys.argv[7]  # type: List[str]  # noqa
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
            processed_logs = Ebb._eblocbroker.events.LogRefundRequest().processReceipt(receipt, errors=DISCARD)
            log(vars(processed_logs[0].args))
            try:
                log(f"refunded_wei={processed_logs[0].args['refundedWei']}")
                log("SUCCESS", "green")
            except Exception as e:
                logging.error(f"E: Transaction is reverted. {e}")
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)
        sys.exit(1)
