#!/usr/bin/env python3

from contextlib import suppress

from web3._utils.threads import Timeout
from web3.types import TxReceipt

from broker import cfg
from broker._utils._log import log, ok
from brownie.network.transaction import TransactionReceipt


def get_tx_status(tx_hash, is_verbose=False) -> TxReceipt:
    """Return status of the transaction."""
    if not tx_hash:
        raise Exception("warning: tx_hash is empty")

    if isinstance(tx_hash, TransactionReceipt):
        tx_hash = tx_hash.txid

    if not is_verbose:
        log(f"tx_hash={tx_hash}")

    try:
        tx_receipt = cfg.Ebb._wait_for_transaction_receipt(tx_hash, is_verbose=is_verbose)
        tx_receipt_dict = dict(tx_receipt)
        if not is_verbose:
            with suppress(Exception):
                del tx_receipt_dict["logsBloom"]

            log("tx=", end="")
            del tx_receipt_dict["contractAddress"]  # not required
            log(tx_receipt_dict, max_depth=1)
            if cfg.TX_LOG_VERBOSE:
                # TODO: many logs show up investigate the reason for this, for exampole submit job has 3 to 5 events
                for idx, tx_log in enumerate(tx_receipt_dict["logs"]):  # all logs that are emitted under the Tx
                    tx_log = dict(tx_log)
                    with suppress(Exception):
                        del tx_log["data"]

                    log(f"[blue]log_{idx}[/blue]=", end="")
                    log(tx_log)

            log("#> Is transaction successfully deployed?", end="")

        if tx_receipt["status"] == 1:
            if not is_verbose:
                log(ok())
        else:
            if not is_verbose:
                log()

            raise Exception("tx is reverted")

        return tx_receipt
    except Timeout as e:
        log(f"E: {e}")
        raise e
    except Exception as e:
        raise e
