#!/usr/bin/env python3

import sys
import traceback

from config import env, logging  # noqa: F401
from lib import get_tx_status
from utils import _colorize_traceback


def refund(self, provider, _from, job_key, index, job_id, cores, execution_durations):
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
        tx = self.eBlocBroker.functions.refund(provider, job_key, index, job_id, cores, execution_durations).transact(
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
        cores = sys.argv[6]
        execution_durations = sys.argv[7]
    else:
        provider = Ebb.w3.toChecksumAddress(env.PROVIDER_ID)
        _from = Ebb.w3.toChecksumAddress(env.PROVIDER_ID)
        job_key = "QmXFVGtxUBLfR2cYPNQtUjRxMv93yzUdej6kYwV1fqUD3U"
        index = 0
        job_id = 0
        cores = [1]  #
        execution_durations = [5]  #

    try:
        tx_hash = Ebb.refund(provider, _from, job_key, index, job_id, cores, execution_durations)
        receipt = get_tx_status(tx_hash)
        if receipt["status"] == 1:
            logs = Ebb.eBlocBroker.events.LogJob().processReceipt(receipt)
            try:
                logging.info(f"Job's index={logs[0].args['index']}")
            except Exception:
                logging.error("E: Transaction is reverted")
    except:
        logging.error(traceback.format_exc())
        sys.exit(1)
