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
from broker._watch.test_info import data_hashes
from broker.eblocbroker_scripts.utils import Cent
from broker.errors import QuietExit
from broker.lib import state

cfg.NETWORK_ID = "bloxberg_core"
Ebb = cfg.Ebb
columns_size = 30
is_while = True  # to fetch on-going results
is_provider = True

#: fetch results into google-sheets and analyze
is_csv = False
analyze_long_test = False

# latest: 20070624
if is_csv:
    is_while = False
    analyze_long_test = True


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
    log("\r" + "=" * columns_size + "[bold] providers [/bold]" + "=" * columns_size, "g")
    for k, v in providers_info.items():
        log(f"** provider_address={k}", end="\r")
        log(v, end="\r")


def print_in_csv_format(job, _id, state_val, workload_type, _hash, _index, title_flag):
    _job = {}
    _job["id"] = f"j{_id + 1}"
    _job["hash"] = _hash
    _job["index"] = _index
    _job["workload"] = workload_type
    _job["state"] = state_val
    _job["core"] = job["core"][0]

    received_bn = job["received_bn"]
    _job["received_bn"] = received_bn
    block = Ebb.get_block(received_bn)

    _job["received_block_ts"] = block["timestamp"]
    _job["start_ts"] = job["start_timestamp"]
    _job["wait_time_(sec)"] = max(_job["start_ts"] - _job["received_block_ts"], 0)
    _job["elapsed_time_(min)"] = job["actual_elapsed_time"]
    _job["used_registed_data"] = None
    _job["price_core_min_usd"] = Cent(job["price_core_min"])._to()
    _job["price_data_transfer_cent"] = Cent(job["price_data_transfer"])._to("cent")
    _job["price_storage_cent"] = Cent(job["price_storage"])._to("cent")
    _job["price_cache_cent"] = Cent(job["price_cache"])._to("cent")
    _job["expected_run_time_(min)"] = job["run_time"][0]
    _job["total_payment_usd"] = Cent(job["submitJob_received_job_price"])._to()
    _job["refunded_usd_to_requester"] = Cent(job["refunded_cent"])._to()
    _job["received_usd_to_provider"] = Cent(job["received_cent"])._to()
    temp_list = []
    if len(job["code_hashes"]) > 1:
        for itm in sorted(job["code_hashes"]):
            try:
                data_hash = itm.decode("utf-8")
                if data_hash in data_hashes:
                    data_alias = data_hashes[data_hash]
                    temp_list.append(data_alias)
                    _job["used_registed_data"] = data_alias
            except:
                pass

    if temp_list:
        _job["used_registed_data"] = ";".join(temp_list)

    tx_receipt = Ebb.get_transaction_receipt(job["submitJob_tx_hash"])
    tx_by_block = Ebb.get_transaction_by_block(tx_receipt["blockHash"].hex(), tx_receipt["transactionIndex"])
    #: decode input arguments
    output = Ebb.eBlocBroker.decode_input(tx_by_block["input"])
    data_transfer_in_arg = str(output[1][1]).replace(" ", "").replace(",", ";")
    _job["data_transfer_in_arg_(MB)"] = data_transfer_in_arg
    _job["data_transfer_out_expected_(MB)"] = output[1][2][7]
    #
    _job["submitJob_tx_hash"] = job["submitJob_tx_hash"]
    _job["submitJob_gas_used"] = job["submitJob_gas_used"]
    _job["processPayment_tx_hash"] = job["processPayment_tx_hash"]
    _job["processPayment_gas_used"] = job["processPayment_gas_used"]
    #
    if title_flag:
        log("", is_write=False)
        title_flag = False
        for idx, (k, v) in enumerate(_job.items()):
            log(f"{k}", h=False, end="")
            if idx == len(_job) - 1:
                log()
            else:
                log(", ", end="")

    for idx, (k, v) in enumerate(_job.items()):
        log(f"{v}", h=False, end="")
        if idx == len(_job) - 1:
            log()
        else:
            log(", ", end="")

    value = float(_job["total_payment_usd"])
    spent = float(_job["refunded_usd_to_requester"]) + float(_job["received_usd_to_provider"])
    delta = value - spent
    if abs(delta) > 0:
        log("warning: ", end="")

    if value != spent:
        delta = "%0.8f" % (delta)
        log(f"delta={delta} value={value} spent={spent}")

    # breakpoint()  # DEBUG


def _watch(eth_address, from_block, is_provider):
    _log.ll.LOG_FILENAME = Path.home() / ".ebloc-broker" / f"watch_{eth_address}.out"
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
    header = f"  [y]{'{:<46}'.format('key')} index       status[/y]"
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

        workload_type = ""
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
            if is_while:
                job_full = (
                    f"[bold blue]*[/bold blue] [white]{'{:<50}'.format(_hash)}[/white] "
                    f"{_index} {'{:<4}'.format(workload_type)}  [{c}]{state_val}[/{c}]\n{job_full}"
                )
            else:
                job_full = (
                    f"[bold blue]*[/bold blue] [bold white]{'{:<50}'.format(_hash)}[/bold white] "
                    f"{_index} {'{:<4}'.format(workload_type)}  [{c}]{state_val}[/{c}]"
                )
                log(job_full)
        else:
            print_in_csv_format(_job, idx, state_val, workload_type, _hash, _index, title_flag)
            title_flag = False

        time.sleep(0.2)

    if is_while:
        job_full = f"{header}\n{job_full}".rstrip()
    elif not is_csv:
        job_ruler = "[g]" + "=" * columns_size + "[bold cyan] jobs [/bold cyan]" + "=" * columns_size + "[/g]"
        job_full = f"{job_ruler}\n{header}\n{job_full}".rstrip()

    is_connected = Ebb.is_web3_connected()
    if is_while:
        _console_clear()

    if not is_csv:
        open(_log.ll.LOG_FILENAME, "w").close()  # clean file right before write into it again

    if is_csv:
        log()

    log(f"\r{_date()} bn={bn} | web3={is_connected} | address={eth_address} | {completed_count}/{job_count}")
    if analyze_long_test:
        log(f"workload_cppr_count={workload_cppr_completed}/{workload_cppr_count}")
        log(f"workload_nas_count={workload_nas_completed}/{workload_nas_count}")

    # get_providers_info()
    log(job_full, is_output=False)


def watch(eth_address="", from_block=None):
    if not from_block:
        from_block = Ebb.get_block_number() - cfg.ONE_DAY_BLOCK_DURATION

    if not eth_address:
        try:
            eth_address = get_eth_address_from_cfg()
        except Exception:
            log("E: eth_address is empty, run as: [m]./watch.py <eth_address>", h=False)
            sys.exit(1)

    watch_fn = Path.home() / ".ebloc-broker" / f"watch_{eth_address}.out"
    open(watch_fn, "w").close()
    _console_clear()
    if is_provider:
        log(f"* starting for provider={eth_address} from_block={from_block}")

    if is_while:
        while True:
            _watch(eth_address, from_block, is_provider)
            time.sleep(30)
    else:
        _watch(eth_address, from_block, is_provider)


def main():
    eth_address = None
    if len(sys.argv) == 2:
        eth_address = sys.argv[1]

    from_block = 20399183
    watch(eth_address, from_block)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print_tb(e)
