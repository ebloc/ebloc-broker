#!/usr/bin/env python3

from broker.eblocbroker_scripts import Contract
from broker._utils._log import log
from broker._utils.tools import print_tb
from broker.errors import QuietExit
import pickle
from pathlib import Path
from broker import cfg
from broker.eblocbroker_scripts.utils import Cent

Ebb: "Contract.Contract" = cfg.Ebb


def read_txs_layer(n, edges):
    checked = {}
    BASE = Path.home() / "test_eblocbroker" / "workflow" / f"{n}_{edges}"
    try:
        with open(BASE / "layer_submitted_dict.pkl", "rb") as f:
            loaded_dict = pickle.load(f)
    except Exception as e:
        print_tb(e)

    total_submitjob_gas = 0
    total_processpayment_gas = 0
    total_received = 0
    total_refunded = 0
    for k, v in loaded_dict.items():
        keys = v.split("_")

        provider = "0x29e613B04125c16db3f3613563bFdd0BA24Cb629"
        job_key = "QmQF75UmtBvnZEZFr1iRLUmb5vt5XXqZqdTkrDKdgXfk8q"
        index = 0
        received_bn = 22301335
        event_filter = Ebb._eblocbroker.events.LogProcessPayment.createFilter(
            argument_filters={"provider": str(provider)},
            fromBlock=int(received_bn),
            toBlock="latest",
        )
        for logged_receipt in event_filter.get_all_entries():
            if logged_receipt.args["jobKey"] == job_key and logged_receipt.args["index"] == int(index):
                log(logged_receipt.args)
                log()

        breakpoint()  # DEBUG
        output = Ebb.get_job_info(keys[0], keys[1], keys[2], 0, keys[3], is_print=False)
        checked_key = f"{keys[0]}_{keys[1]}_{keys[2]}_{keys[3]}"
        if checked_key not in checked:
            checked[checked_key] = True
            total_submitjob_gas += output["submitJob_gas_used"]
            total_processpayment_gas += output["processPayment_gas_used"]
            total_received += output["received_cent"]
            total_refunded += output["refunded_cent"]
            log(f"{k} => ", end="")
            log(v)

    log(f"LAYER {n} {edges}")
    log(f"total_submitjob_gas={total_submitjob_gas}")
    log(f"total_processpayment_gas={total_processpayment_gas}")
    log(f"total_received={Cent(total_received)._to()} [pink]USDmy")
    log(f"total_refunded={Cent(total_refunded)._to()} [pink]USDmy")
    log("--------------------------------------------------------")


def read_txs(n, edges):
    BASE = Path.home() / "test_eblocbroker" / "workflow" / f"{n}_{edges}"
    try:
        with open(BASE / "heft_submitted_dict.pkl", "rb") as f:
            loaded_dict = pickle.load(f)
    except Exception as e:
        print_tb(e)

    total_submitjob_gas = 0
    total_received = 0
    total_refunded = 0
    sum_received = 0
    sum_refunded = 0
    total_processpayment_gas = 0
    for k, v in loaded_dict.items():
        keys = k.split("_")

        provider = keys[0]
        job_key = keys[1]
        index = keys[2]
        received_bn = keys[3]
        event_filter = Ebb._eblocbroker.events.LogProcessPayment.createFilter(
            argument_filters={"provider": str(provider)},
            fromBlock=int(received_bn),
            toBlock="latest",
        )
        for logged_receipt in event_filter.get_all_entries():
            if logged_receipt.args["jobKey"] == job_key and logged_receipt.args["index"] == int(index):
                sum_received += logged_receipt.args["receivedCent"]
                sum_refunded += logged_receipt.args["refundedCent"]
                tx_receipt = Ebb.get_transaction_receipt(logged_receipt["transactionHash"].hex())
                print(int(tx_receipt["gasUsed"]))
                total_processpayment_gas += int(tx_receipt["gasUsed"])
                # log(logged_receipt.args)
                # log()

        output = Ebb.get_job_info(keys[0], keys[1], keys[2], 0, keys[3], is_print=False)
        _job_price = output["submitJob_received_job_price"]
        total_submitjob_gas += output["submitJob_gas_used"]
        total_received += sum_received
        total_refunded += output["refunded_cent"]
        # log(f"{sum_received} {_job_price}")
        log(f"{k} => ", end="")
        log(f"{v}")

    log()
    log(f"* HEFT {n} {edges}")
    log(f"total_submitjob_gas={total_submitjob_gas}")
    log(f"total_processpayment_gas={total_processpayment_gas}")
    log(f"total_received={Cent(total_received)._to()} [pink]USDmy")
    log(f"total_refunded={Cent(total_refunded)._to()} [pink]USDmy")
    log("--------------------------------------------------------")


def main():
    """
    test = [(20, 25), (40, 50), (60, 72), (80, 100), (100, 125), (120, 150), (140, 200), (160, 225)]
    test = dict(test)
    for n, edges in test.items():
        read_txs(n, edges)

    breakpoint()  # DEBUG
    """
    ###

    # test = [(16, 28), (32, 56), (64, 112), (128, 224), (256, 448)]
    test = [(16, 28)]
    test = dict(test)
    for n, edges in test.items():
        read_txs(n, edges)
        # read_txs_layer(n, edges)
        breakpoint()  # DEBUG


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"#> {e}")
    except Exception as e:
        print_tb(str(e))
