#!/usr/bin/env python3

import pickle
from pathlib import Path

from broker import cfg
from broker._utils._log import log
from broker._utils.tools import print_tb
from broker.eblocbroker_scripts import Contract
from broker.eblocbroker_scripts.utils import Cent
from broker.errors import QuietExit

Ebb: "Contract.Contract" = cfg.Ebb

is_excel = True
if is_excel:
    log(
        "type,provider_label,id,sourceCodeHash,index,job_id,received_bn,w_type,elapsed_time,processPayment_tx_hash,"
        "processPayment_gasUsed,submitJob_tx_hash,submitJob_gas_used,data_transfer_in_to_download,data_transfer_out,"
        "job_price"
    )

provider_id = {}
provider_id["0x29e613B04125c16db3f3613563bFdd0BA24Cb629".lower()] = "a"
provider_id["0x4934a70Ba8c1C3aCFA72E809118BDd9048563A24".lower()] = "b"
provider_id["0xe2e146d6B456760150d78819af7d276a1223A6d4".lower()] = "c"


# BASE = Path.home() / "test_eblocbroker" / "workflow" / "HEFT_LAYER_128"
BASE = Path.home() / "test_eblocbroker" / "workflow" / "32_LAYER"


def read_txs_layer(n, edges, fn):
    try:
        with open(BASE / fn, "rb") as f:
            loaded_dict = pickle.load(f)
    except Exception as e:
        print_tb(e)

    name = fn.replace(".pkl", "").replace("submitted_dict_", "")
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
        if int(job_id) == 0:
            output_g = Ebb.get_job_info(keys[0], keys[1], keys[2], 0, keys[3], is_print=False)
            _job_price = output_g["submitJob_received_job_price"]
            jp = float(Cent(_job_price)._to())
            job_price_sum += jp
            total_submitjob_gas += output_g["submitJob_gas_used"]
            total_refunded += sum_refunded  # output_g["refunded_cent"]

        for logged_receipt in event_filter.get_all_entries():
            if (
                logged_receipt.args["jobKey"] == job_key
                and logged_receipt.args["index"] == int(index)
                and logged_receipt.args["jobID"] == int(job_id)
            ):
                output = Ebb.get_job_info(keys[0], keys[1], keys[2], job_id, keys[3], is_print=False)
                idx += 1
                recv = logged_receipt.args["receivedCent"]
                ref = logged_receipt.args["refundedCent"]
                sum_received += float(Cent(recv)._to())
                sum_refunded += float(Cent(ref)._to())
                tx_receipt = Ebb.get_transaction_receipt(logged_receipt["transactionHash"].hex())
                total_processpayment_gas += int(tx_receipt["gasUsed"])
                if is_excel:
                    if int(job_id) == 0:
                        log(
                            f"{name},{provider_id[provider.lower()]},j{idx},{job_key},{index},{job_id},{received_bn},{n}_{edges},{output['run_time'][int(job_id)]},"
                            f"{tx_receipt['transactionHash'].hex()},{tx_receipt['gasUsed']},{output_g['submitJob_tx_hash']},{output_g['submitJob_gas_used']},"
                            f"{output_g['data_transfer_in_to_download']},{output_g['data_transfer_out']},{jp}"
                        )
                    else:
                        log(
                            f"{name},{provider_id[provider.lower()]},j{idx},{job_key},{index},{job_id},{received_bn},{n}_{edges},{output['run_time'][int(job_id)]},"
                            f"{tx_receipt['transactionHash'].hex()},{tx_receipt['gasUsed']}"
                        )

    if not is_excel:
        log(f"LAYER {n} {edges}")
        log(f"total_submitjob_gas={total_submitjob_gas}")
        log(f"total_processpayment_gas={total_processpayment_gas} idx={idx}")
        log(f"total_received={sum_received} [pink]USDmy")
        log(f"total_refunded={Cent(total_refunded)._to()} [pink]USDmy")
        log(f"job_price_sum={job_price_sum}")
        log("--------------------------------------------------------")


def read_txs(n, edges, fn):
    try:
        with open(BASE / fn, "rb") as f:
            loaded_dict = pickle.load(f)
    except Exception as e:
        print_tb(e)

    name = fn.replace(".pkl", "").replace("submitted_dict_", "")
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
        output_g = Ebb.get_job_info(keys[0], keys[1], keys[2], 0, keys[3], is_print=False)
        _job_price = output_g["submitJob_received_job_price"]
        jp = float(Cent(_job_price)._to())
        job_price_sum += jp
        total_submitjob_gas += output_g["submitJob_gas_used"]
        total_refunded += sum_refunded  # output_g["refunded_cent"]
        # log(f"{sum_received} {_job_price}")
        # log(f"{k} => ", end="")
        # log(f"{v}")
        for logged_receipt in event_filter.get_all_entries():
            if logged_receipt.args["jobKey"] == job_key and logged_receipt.args["index"] == int(index):
                idx += 1
                job_id = logged_receipt.args["jobID"]
                output = Ebb.get_job_info(keys[0], keys[1], keys[2], job_id, keys[3], is_print=False)
                recv = logged_receipt.args["receivedCent"]
                # log(f"{Cent(recv)._to()} [pink]USDmy")
                sum_received += float(Cent(recv)._to())
                sum_refunded += logged_receipt.args["refundedCent"]
                tx_receipt = Ebb.get_transaction_receipt(logged_receipt["transactionHash"].hex())
                total_processpayment_gas += int(tx_receipt["gasUsed"])
                if is_excel:
                    if job_id == 0:
                        log(
                            f"{name},{provider_id[provider.lower()]},j{idx},{job_key},{index},{job_id},{received_bn},{n}_{edges},{output['run_time'][job_id]},"
                            f"{tx_receipt['transactionHash'].hex()},{tx_receipt['gasUsed']},{output_g['submitJob_tx_hash']},{output_g['submitJob_gas_used']},"
                            f"{output_g['data_transfer_in_to_download']},{output_g['data_transfer_out']},{jp}"
                        )
                    else:
                        log(
                            f"{name},{provider_id[provider.lower()]},j{idx},{job_key},{index},{job_id},{received_bn},{n}_{edges},{output['run_time'][job_id]},"
                            f"{tx_receipt['transactionHash'].hex()},{tx_receipt['gasUsed']}"
                        )

                # print(logged_receipt.args["receivedCent"])
                # print(int(tx_receipt["gasUsed"]))
                # log(logged_receipt.args)
                # log()

    if not is_excel:
        log()
        log(f"* HEFT {n} {edges}")
        log(f"total_submitjob_gas={total_submitjob_gas}")
        log(f"total_processpayment_gas={total_processpayment_gas} idx={idx}")
        log(f"total_received={sum_received} [pink]USDmy")
        log(f"total_refunded={Cent(total_refunded)._to()} [pink]USDmy")
        log(f"job_price_sum={job_price_sum}")
        log("--------------------------------------------------------")


def main():
    test = [(16, 28), (32, 56), (64, 112), (128, 224), (256, 448)]
    # test = [(16, 28)]
    test = [(32, 56)]
    # test = [(64, 112)]
    # test = [(128, 224)]
    # test = [(256, 448)]
    test = dict(test)
    for n, edges in test.items():
        """
        read_txs(n, edges, "heft_submitted_dict_hoe2_1.pkl")
        log("\n\n\n")
        read_txs(n, edges, "heft_submitted_dict_hoe2_2.pkl")
        log("\n\n\n")
        read_txs(n, edges, "heft_submitted_dict_hoe2_3.pkl")
        """
        # ====================================================================
        """
        read_txs_layer(n, edges, "layer_submitted_dict_1.pkl")
        log("\n\n\n")
        read_txs_layer(n, edges, "layer_submitted_dict_2.pkl")
        log("\n\n\n")
        read_txs_layer(n, edges, "layer_submitted_dict_3.pkl")
        """
        read_txs_layer(n, edges, "layer_submitted_dict_hoe2_1.pkl")
        log("\n\n\n")
        read_txs_layer(n, edges, "layer_submitted_dict_hoe2_2.pkl")
        log("\n\n\n")
        read_txs_layer(n, edges, "layer_submitted_dict_hoe2_3.pkl")

        if not is_excel:
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
