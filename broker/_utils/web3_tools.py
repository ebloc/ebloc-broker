#!/usr/bin/env python3

from contextlib import suppress

from web3._utils.threads import Timeout
from web3.types import TxReceipt

from broker import cfg
from broker._utils._log import log, ok
from brownie.network.transaction import TransactionReceipt


def get_tx_status(tx_hash, is_silent=False) -> TxReceipt:
    """Return status of the transaction."""
    if not tx_hash:
        raise Exception("warning: tx_hash is empty")

    if isinstance(tx_hash, TransactionReceipt):
        tx_hash = tx_hash.txid

    if not is_silent:
        log(f"tx_hash={tx_hash}", "bold")

    try:
        tx_receipt = cfg.Ebb._wait_for_transaction_receipt(tx_hash, is_silent=is_silent)
        _tx_receipt = dict(tx_receipt)
        if not is_silent:
            with suppress(Exception):
                del _tx_receipt["logsBloom"]

            log("tx=", "bold", end="")
            log(_tx_receipt, max_depth=1)
            for idx, _log in enumerate(_tx_receipt["logs"]):  # All logs fried under the tx
                _log = dict(_log)
                with suppress(Exception):
                    del _log["data"]

                log(f"log_{idx}=", "bold blue", end="")
                log(_log)

            log("#> Was transaction successfully deployed? ", end="")

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
