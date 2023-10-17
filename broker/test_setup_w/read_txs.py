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


def read_txs_layer(n, edges, fn):
    checked = {}
    BASE = Path.home() / "test_eblocbroker" / "workflow" / f"{n}_{edges}"
    try:
        with open(BASE / fn, "rb") as f:
            loaded_dict = pickle.load(f)
    except Exception as e:
        print_tb(e)

    job_price_sum = 0
    sum_received = 0
    sum_refunded = 0
    total_processpayment_gas = 0
    idx = 0
    total_submitjob_gas = 0
    total_processpayment_gas = 0
    total_refunded = 0
    # for k, v in loaded_dict.items():
    #     log(f"{v} => {k}")

    for k, v in loaded_dict.items():
        keys = v.split("_")
        provider = keys[0]
        job_key = keys[1]
        index = keys[2]
        received_bn = keys[3]
        job_id = keys[4]
        event_filter = Ebb._eblocbroker.events.LogProcessPayment.createFilter(
            argument_filters={"provider": str(provider)},
            fromBlock=int(received_bn),
            toBlock="latest",
        )
        for logged_receipt in event_filter.get_all_entries():
            if (
                logged_receipt.args["jobKey"] == job_key
                and logged_receipt.args["index"] == int(index)
                and logged_receipt.args["jobID"] == int(job_id)
            ):
                idx += 1
                recv = logged_receipt.args["receivedCent"]
                ref = logged_receipt.args["refundedCent"]
                sum_received += float(Cent(recv)._to())
                sum_refunded += float(Cent(ref)._to())
                tx_receipt = Ebb.get_transaction_receipt(logged_receipt["transactionHash"].hex())
                total_processpayment_gas += int(tx_receipt["gasUsed"])

        if int(job_id) == 0:
            output = Ebb.get_job_info(keys[0], keys[1], keys[2], 0, keys[3], is_print=False)
            _job_price = output["submitJob_received_job_price"]
            job_price_sum += float(Cent(_job_price)._to())
            total_submitjob_gas += output["submitJob_gas_used"]
            total_refunded += sum_refunded  # output["refunded_cent"]

    log(f"LAYER {n} {edges}")
    log(f"total_submitjob_gas={total_submitjob_gas}")
    log(f"total_processpayment_gas={total_processpayment_gas} idx={idx}")
    log(f"total_received={sum_received} [pink]USDmy")
    log(f"total_refunded={Cent(total_refunded)._to()} [pink]USDmy")
    log(f"job_price_sum={job_price_sum}")
    log("--------------------------------------------------------")


def read_txs(n, edges, fn):
    BASE = Path.home() / "test_eblocbroker" / "workflow" / f"{n}_{edges}"
    try:
        with open(BASE / fn, "rb") as f:
            loaded_dict = pickle.load(f)
    except Exception as e:
        print_tb(e)

    job_price_sum = 0
    total_submitjob_gas = 0
    total_refunded = 0
    sum_received = 0
    sum_refunded = 0
    total_processpayment_gas = 0
    idx = 0
    for k, v in loaded_dict.items():
        # log(f"{k} => {v}")
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
                idx += 1
                recv = logged_receipt.args["receivedCent"]
                # log(f"{Cent(recv)._to()} [pink]USDmy")
                sum_received += float(Cent(recv)._to())
                sum_refunded += logged_receipt.args["refundedCent"]
                tx_receipt = Ebb.get_transaction_receipt(logged_receipt["transactionHash"].hex())
                total_processpayment_gas += int(tx_receipt["gasUsed"])
                # print(logged_receipt.args["receivedCent"])
                # print(int(tx_receipt["gasUsed"]))
                # log(logged_receipt.args)
                # log()

        output = Ebb.get_job_info(keys[0], keys[1], keys[2], 0, keys[3], is_print=False)
        _job_price = output["submitJob_received_job_price"]
        job_price_sum += float(Cent(_job_price)._to())
        total_submitjob_gas += output["submitJob_gas_used"]
        total_refunded += sum_refunded  # output["refunded_cent"]
        # log(f"{sum_received} {_job_price}")
        # log(f"{k} => ", end="")
        # log(f"{v}")

    log()
    log(f"* HEFT {n} {edges}")
    log(f"total_submitjob_gas={total_submitjob_gas}")
    log(f"total_processpayment_gas={total_processpayment_gas} idx={idx}")
    log(f"total_received={sum_received} [pink]USDmy")
    log(f"total_refunded={Cent(total_refunded)._to()} [pink]USDmy")
    log(f"job_price_sum={job_price_sum}")
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

    test = [(16, 28), (32, 56), (64, 112), (128, 224), (256, 448)]
    # test = [(16, 28)]
    # test = [(32, 56)]
    # test = [(64, 112)]
    test = dict(test)
    for n, edges in test.items():
        # read_txs(n, edges, "heft_submitted_dict_1.pkl")
        # read_txs(n, edges, "heft_submitted_dict_2.pkl")
        # read_txs(n, edges, "heft_submitted_dict_3.pkl")
        # -----------------------------------------------------
        read_txs_layer(n, edges, "layer_submitted_dict_1.pkl")
        read_txs_layer(n, edges, "layer_submitted_dict_2.pkl")
        read_txs_layer(n, edges, "layer_submitted_dict_3.pkl")
        log("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-", "yellow")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"#> {e}")
    except Exception as e:
        print_tb(str(e))
