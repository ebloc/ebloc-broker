#!/usr/bin/env python3

from web3._utils.threads import Timeout
from web3.types import TxReceipt

from broker import cfg
from broker._utils._log import log, ok


def get_tx_status(tx_hash: str, is_silent=False) -> TxReceipt:
    """Return status of the transaction."""
    if not is_silent:
        log(f"tx_hash={tx_hash}", "bold")

    try:
        tx_receipt = cfg.Ebb._wait_for_transaction_receipt(tx_hash, is_silent=is_silent)
        if not is_silent:
            log("tx=", "bold", end="")
            log(tx_receipt)
            log("#> Was transaction successfully deployed? ", end="")

        # pprint(dict(tx_receipt), depth=1)
        # for idx, _log in enumerate(receipt["logs"]):
        #     # All logs fried under the tx
        #     log(f"log {idx}", "blue")
        #     pprint(_log.__dict__)
        if tx_receipt["status"] == 1:
            if not is_silent:
                log(ok())
        else:
            if not is_silent:
                log()

            raise Exception("E: Transaction is reverted")

        return tx_receipt
    except Timeout as e:
        log(str(e))
        raise e
    except Exception as e:
        raise e