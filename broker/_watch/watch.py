#!/usr/bin/env python3

"""Job watcher for the end of test."""

import os
import sys
import time
from pathlib import Path

from broker import cfg
from broker._utils import _log
from broker._utils._log import _console_clear
from broker._utils.tools import _date, log, print_tb
from broker._utils.yaml import Yaml
from broker.errors import QuietExit
from broker.lib import state
from broker._watch.test_info import data_hashes


Ebb = cfg.Ebb
columns_size = 30
is_get_ongoing_test_results = False
is_log_to_file = True
is_csv = True


def get_eth_address_from_cfg():
    hidden_base_dir = Path.home() / ".ebloc-broker"
    fn = hidden_base_dir / "cfg.yaml"
    if not os.path.isfile(fn):
        if not os.path.isdir(hidden_base_dir):
            raise QuietExit(f"E: {hidden_base_dir} is not initialized")

        raise QuietExit(f"E: {fn} is not created")

    cfg_yaml = Yaml(fn)
    cfg = cfg_yaml["cfg"]
    return cfg.w3.toChecksumAddress(cfg["eth_address"].lower())


def get_providers_info():
    # from broker.test_setup.user_set import providers
    providers_info = {}
    providers = Ebb.get_providers()
    for provider_addr in providers:
        providers_info[provider_addr] = Ebb.get_provider_info(provider_addr)

    providers = Ebb.get_providers()
    log("\r" + "=" * columns_size + "[bold] providers [/bold]" + "=" * columns_size, "green")
    for k, v in providers_info.items():
        log(f"** provider_address={k}", end="\r")
        log(v, end="\r")


def print_in_csv_format(job, _id, state_val, workload_type, _hash, _index, title_flag):
    j = {}
    j["id"] = f"j{_id + 1}"
    j["hash"] = _hash
    j["index"] = _index
    j["workload"] = workload_type
    j["state"] = state_val
    j["core"] = job["core"][0]

    received_bn = job["received_bn"]
    j["received_bn"] = received_bn
    block = Ebb.get_block(received_bn)
    #
    j["received_block_ts"] = block["timestamp"]
    j["start_ts"] = job["start_timestamp"]
    j["wait_time_(sec)"] = max(j["start_ts"] - j["received_block_ts"], 0)
    #
    j["elapsed_time_(min)"] = job["actual_elapsed_time"]
    j["used_registed_data"] = "None"
    #
    j["price_cache"] = job["price_cache"]
    j["price_core_min"] = job["price_core_min"]
    j["price_data_transfer"] = job["price_data_transfer"]
    j["price_storage"] = job["price_storage"]
    j["expected_run_time_(min)"] = job["run_time"][0]

    j["total_payment"] = job["submitJob_msg_value"]

    j["refunded_gwei_to_requester"] = job["refunded_gwei"]
    j["received_gwei_to_provider"] = job["received_gwei"]
    temp_list = []
    if len(job["code_hashes"]) > 1:
        for itm in sorted(job["code_hashes"]):
            try:
                data_hash = itm.decode("utf-8")
                if data_hash in data_hashes:
                    data_alias = data_hashes[data_hash]
                    temp_list.append(data_alias)
                    j["used_registed_data"] = data_alias
            except:
                pass

    if temp_list:
        j["used_registed_data"] = ";".join(temp_list)

    tx_receipt = Ebb.get_transaction_receipt(job["submitJob_tx_hash"])
    tx_by_block = Ebb.get_transaction_by_block(tx_receipt["blockHash"].hex(), tx_receipt["transactionIndex"])
    output = Ebb.eBlocBroker.decode_input(tx_by_block["input"])
    data_transfer_in_arg = str(output[1][1]).replace(" ", "").replace(",", ";")
    j["data_transfer_in_arg_(MB)"] = data_transfer_in_arg
    j["data_transfer_out_expected_(MB)"] = output[1][2][7]
    #
    j["submitJob_tx_hash"] = job["submitJob_tx_hash"]
    j["submitJob_gas_used"] = job["submitJob_gas_used"]
    j["processPayment_tx_hash"] = job["processPayment_tx_hash"]
    j["processPayment_gas_used"] = job["processPayment_gas_used"]
    #
    if title_flag:
        title_flag = False
        for idx, (k, v) in enumerate(j.items()):
            log(f"{k}", end="")
            if idx == len(j) - 1:
                log()
            else:
                log(", ", end="")

    for idx, (k, v) in enumerate(j.items()):

        log(f"{v}", end="")
        if idx == len(j) - 1:
            log()
        else:
            log(", ", end="")

    # breakpoint()  # DEBUG


def _watch(eth_address, from_block, is_provider):
    _log.ll.LOG_FILENAME = f"provider_{eth_address}.txt"
    open(_log.ll.LOG_FILENAME, "w").close()
    bn = Ebb.get_block_number()
    if is_provider:
        _argument_filters = {"provider": eth_address}
    else:
        _argument_filters = {"owner": eth_address}

    event_filter = Ebb._eblocbroker.events.LogJob.createFilter(
        fromBlock=int(from_block),
        argument_filters=_argument_filters,
        toBlock="latest",
    )
    header = f"   [bold yellow]{'{:<44}'.format('KEY')} INDEX STATUS[/bold yellow]"
    job_full = ""
    job_count = 0
    completed_count = 0
    workload_cppr_completed = 0
    workload_nas_completed = 0
    workload_cppr_count = 0
    workload_nas_count = 0
    title_flag = True
    for idx, job in enumerate(event_filter.get_all_entries()):
        job_count += 1
        try:
            _args = job["args"]
        except:
            job = job[1]
            _args = job["args"]

        _job = Ebb.get_job_info(
            _args["provider"],
            _args["jobKey"],
            _args["index"],
            0,
            job["blockNumber"],
            is_print=False,
            is_fetch_code_hashes=True,
        )
        state_val = state.inv_code[_job["stateCode"]]
        c = "magenta"
        if state_val == "COMPLETED":
            c = "green"
            completed_count += 1

        if len(_job["code_hashes"]) == 4:
            workload_cppr_count += 1
            workload_type = "cppr"
            if state_val == "COMPLETED":
                workload_cppr_completed += 1
        elif len(_job["code_hashes"]) == 1:
            workload_nas_count += 1
            workload_type = "nas"
            if state_val == "COMPLETED":
                workload_nas_completed += 1
        else:
            print("ALERT")

        _hash = _job["job_key"]
        _index = _job["index"]
        if not is_csv:
            if is_get_ongoing_test_results:
                job_full = (
                    f" [bold blue]*[/bold blue] [bold white]{'{:<48}'.format(_hash)}[/bold white] "
                    f"{_index} {workload_type} [bold {c}]{state_val}[/bold {c}]\n{job_full}"
                )
            else:
                job_full = (
                    f" [bold blue]*[/bold blue] [bold white]{'{:<48}'.format(_hash)}[/bold white] "
                    f"{_index} {workload_type} [bold {c}]{state_val}[/bold {c}]"
                )
                log(job_full)
        else:
            print_in_csv_format(_job, idx, state_val, workload_type, _hash, _index, title_flag)
            title_flag = False

        time.sleep(0.2)

    if is_get_ongoing_test_results:
        job_full = f"{header}\n{job_full}".rstrip()
    else:
        job_ruler = "[green]" + "=" * columns_size + "[bold cyan] jobs [/bold cyan]" + "=" * columns_size + "[/green]"
        job_full = f"{job_ruler}\n{header}\n{job_full}".rstrip()

    is_connected = Ebb.is_web3_connected()
    if is_get_ongoing_test_results:
        _console_clear()

    log(
        f"\r==> {_date()} bn={bn} | web3={is_connected} | address={eth_address} | {completed_count}/{job_count}",
        "bold",
    )
    log(f"workload_cppr_count={workload_cppr_completed}/{workload_cppr_count}", "b")
    log(f"workload_nas_count={workload_nas_completed}/{workload_nas_count}", "b")
    # get_providers_info()
    log(job_full, is_output=False)


def watch(eth_address="", from_block=None):
    if not from_block:
        from_block = Ebb.get_block_number() - cfg.ONE_DAY_BLOCK_DURATION

    from_block = 15867616
    if not eth_address:
        try:
            eth_address = get_eth_address_from_cfg()
        except Exception as e:
            log(f"E: {e}\neth_address is empty, run as: [m]./watch.py <eth_address>")
            sys.exit(1)

    if is_log_to_file:
        watch_fn = Path.home() / ".ebloc-broker" / f"watch_{eth_address}.out"
        open(watch_fn, "w").close()
        _log.ll.LOG_FILENAME = watch_fn

    _console_clear()
    log(f" * starting for provider={eth_address}")
    is_provider = True

    if is_get_ongoing_test_results:
        while True:
            _watch(eth_address, from_block, is_provider)
            log()
            time.sleep(2)
    else:
        _watch(eth_address, from_block, is_provider)


def main():
    eth_address = None
    if len(sys.argv) == 2:
        eth_address = sys.argv[1]

    watch(eth_address)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print_tb(e)
