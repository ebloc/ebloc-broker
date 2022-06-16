#!/usr/bin/env python3

import os.path
import random
import sys
from datetime import datetime
from pathlib import Path
from random import randint

from pymongo import MongoClient
from web3.logs import DISCARD

from broker import cfg
from broker._utils import _log
from broker._utils._log import console_ruler
from broker._utils.tools import _date, _timestamp, countdown, is_process_on, log, run
from broker._utils.web3_tools import get_tx_status
from broker._utils.yaml import Yaml
from broker.libs import gdrive
from broker.libs.mongodb import BaseMongoClass
from broker.submit_base import SubmitBase
from broker.test_setup.user_set import providers, requesters
from broker.utils import print_tb

Ebb = cfg.Ebb
cfg.IS_FULL_TEST = True
is_mini_test = True

mc = MongoClient()
ebb_mongo = BaseMongoClass(mc, mc["ebloc_broker"]["tests"])
_log.ll.LOG_FILENAME = Path.home() / ".ebloc-broker" / "test.log"

benchmarks = ["nas", "cppr"]
storage_ids = ["eudat", "gdrive", "ipfs"]
ipfs_ids = ["ipfs", "ipfs_gpg"]

# for provider_addr in providers:
#     mini_tests_submit(storage_ids, provider_addr)

# if is_mini_test:
#     benchmarks = ["cppr"]
#     storage_ids = ["ipfs"]
#     ipfs_ids = ["ipfs"]
#     providers = ["0x29e613b04125c16db3f3613563bfdd0ba24cb629"]

test_dir = Path.home() / "ebloc-broker" / "broker" / "test_setup"
nas_yaml_fn = test_dir / "job_nas.yaml"
cppr_yam_fn = test_dir / "job_cppr.yaml"


def check_gdrive_user():
    try:
        gdrive.check_gdrive_about("alper.alimoglu.research2@gmail.com")
    except Exception as e:
        print_tb(e)
        sys.exit(1)


def test_with_small_dataset(value):
    fn = os.path.expanduser("~/test_eblocbroker/run_cppr/run.sh")
    with open(fn, "w+") as file:
        changed_filedata = file.read().replace("DATA_HASH='change_folder_hash'", f"DATA_HASH='{value}'")
        file.write(changed_filedata)


def create_cppr_job_script(idx):
    """Create cppr slurm job script to be submitted."""
    # registered_data_hashes_small = [
    #     "f1de03edab51f281815c3c1e5ecb88c6",
    #     "03919732a417cb1d14049844b9de0f47",
    #     "983b9fe8a85b543dd5a4a75d031f1091",
    #     "b6aaf03752dc68d625fc57b451faa2bf",
    #     "c0fee5472f3c956ba759fd54f1fe843e",
    #     "63ffd1da6122e3fe9f63b1e7fcac1ff5",
    #     "9e8918ff9903e3314451bf2943296d31",
    #     "eaf488aea87a13a0bea5b83a41f3d49a",
    #     "e62593609805db0cd3a028194afb43b1",
    #     "3b0f75445e662dc87e28d60a5b13cd43",
    #     "ebe53bd498a9f6446cd77d9252a9847c",
    #     "f82aa511f8631bfc9a82fe6fa30f4b52",
    #     "082d2a71d86a64250f06be14c55ca27e",
    #     "f93b9a9f63447e0e086322b8416d4a39",
    #     "761691119cedfb9836a78a08742b14cc",
    # ]
    registered_data_hashes_medium = {}
    registered_data_hashes_medium[0] = [
        "fe801973c5b22ef6861f2ea79dc1eb9c",  # A
        "0d6c3288ef71d89fb93734972d4eb903",  # A
        "4613abc322e8f2fdeae9a5dd10f17540",  # A
    ]
    registered_data_hashes_medium[1] = [
        "050e6cc8dd7e889bf7874689f1e1ead6",  # B
        "9d5d892a63b5758090258300a59eb389",  # B
        "779745f315060d1bc0cd44b7266fb4da",  # B
    ]
    registered_data_hashes_medium[2] = [
        "dd0fbccccf7a198681ab838c67b68fbf",  # C
        "45281dfec4618e5d20570812dea38760",  # C
        "bfc83d9f6d5c3d68ca09499190851e86",  # C
    ]
    registered_data_hashes_medium[3] = [
        "8f6faf6cfd245cae1b5feb11ae9eb3cf",  # D
        "1bfca57fe54bc46ba948023f754521d6",  # D
        "f71df9d36cd519d80a3302114779741d",  # D
    ]
    _list = registered_data_hashes_medium[idx]
    hash_medium_data_0 = random.choice(_list)
    hash_medium_data = random.choice(_list)
    while True:
        if hash_medium_data_0 == hash_medium_data:
            hash_medium_data = random.choice(_list)
        else:
            break

    fn = Path.home() / "test_eblocbroker" / "run_cppr" / "run.sh"
    open(fn, "w").close()
    f = open(fn, "w+")
    f.write("#!/bin/bash\n")
    f.write("#SBATCH -o slurm.out  # STDOUT\n")
    f.write("#SBATCH -e slurm.err  # STDERR\n")
    f.write("#SBATCH --mail-type=ALL\n\n")
    f.write("export OMP_NUM_THREADS=1\n")
    f.write("current_date=$(LANG=en_us_88591; date)\n")
    f.write(f"DATA_HASH='{hash_medium_data_0}'\n")
    f.write("DATA1_DIR='../data_link/'$DATA_HASH'/'\n")
    f.write("echo ' * '$current_date > output.log\n")
    f.write("find $DATA1_DIR -name '*.max' -print0 | while read -d $'\\0' file\n")
    f.write("do\n")
    f.write("    echo $file >> output.log\n")
    f.write("    (/usr/bin/time -v cppr -a pr $file) >> output.log 2>&1\n")
    f.write("done\n")
    f.write(f"DATA_HASH='{hash_medium_data}'\n")
    f.write("DATA2_DIR='../data_link/'$DATA_HASH'/'\n")
    f.write("echo ' * '$current_date >> output.log\n")
    f.write("find $DATA2_DIR -name '*.max' -print0 | while read -d $'\\0' file\n")
    f.write("do\n")
    f.write("    echo $file >> output.log\n")
    f.write("    (/usr/bin/time -v cppr -a pr $file) >> output.log 2>&1\n")
    f.write("done\n")

    # adding cppr to run with data hashes
    f.write("DATA_HASH='change_folder_hash'\n")
    f.write("if [[ '$DATA_HASH' != 'change_folder_hash' ]]; then\n")
    f.write("    DATA3_DIR='../data_link/'$DATA_HASH'/'\n")
    f.write("    echo ' * '$current_date >> output.log\n")
    f.write("    find $DATA3_DIR -name '*.max' -print0 | while read -d $'\\0' file\n")
    f.write("    do\n")
    f.write("        echo $file >> output.log\n")
    f.write("        (/usr/bin/time -v cppr -a pr $file) >> output.log 2>&1\n")
    f.write("    done\n")
    f.write("fi\n")
    f.write("echo '  [  DONE  ]  ' >> output.log\n")
    f.close()
    run(["sed", "-i", r"s/\x0//g", fn])  # remove NULL characters from the SBATCH file
    return hash_medium_data_0, hash_medium_data


def create_nas_job_script(is_small=False):
    """Create NPB3.3-SER slurm job script to be submitted."""
    benchmark_names = ["bt", "cg", "ep", "is", "lu", "sp", "ua"]
    benchmark_name = random.choice(benchmark_names)
    output_fn = "output.log"
    hash_str = random.getrandbits(128)
    fn = Path.home() / "test_eblocbroker" / "NPB3.3-SER_source_code" / "run.sh"
    open(fn, "w").close()
    f = open(fn, "w+")
    f.write("#!/bin/bash\n")
    f.write("#SBATCH -o slurm.out  # STDOUT\n")
    f.write("#SBATCH -e slurm.err  # STDERR\n")
    f.write("#SBATCH --mail-type=ALL\n\n")
    f.write(f"make {benchmark_name} CLASS=A > {output_fn}\n")
    f.write(f"/usr/bin/time -v bin/{benchmark_name}.A.x >> {output_fn}\n")
    f.write("make clean\n")
    f.write("sleep 5\n")
    if not is_small:
        f.write(f"make {benchmark_name} CLASS=B >> {output_fn}\n")
        f.write(f"/usr/bin/time -v bin/{benchmark_name}.B.x >> {output_fn}\n")
        f.write("make clean\n")
        f.write("sleep 5\n")
        f.write(f"make {benchmark_name} CLASS=C >> {output_fn}\n")
        f.write(f"/usr/bin/time -v bin/{benchmark_name}.C.x >> {output_fn}\n")
        f.write("make clean\n")

    f.write(f"# {hash_str}\n")
    f.close()
    run(["sed", "-i", r"s/\x0//g", fn])  # remove NULL characters from the SBATCH file
    return benchmark_name


def mini_tests_submit(storage_ids, provider_addr):
    is_pass = True
    required_confs = 0
    yaml_fn = Path.home() / "ebloc-broker" / "broker" / "test_setup" / "job_nas.yaml"
    yaml_cfg = Yaml(yaml_fn)
    yaml_cfg["config"]["provider_address"] = provider_addr
    for storage_id in storage_ids:
        yaml_cfg["config"]["source_code"]["storage_id"] = storage_id
        benchmark_name = create_nas_job_script(is_small=True)
        submit_base = SubmitBase(yaml_cfg.path)
        tx_hash = submit_base.submit(is_pass, required_confs)
        if required_confs >= 1:
            tx_receipt = get_tx_status(tx_hash, is_verbose=True)
            if tx_receipt["status"] == 1:
                processed_logs = Ebb._eblocbroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
                try:
                    if processed_logs:
                        job_result = vars(processed_logs[0].args)
                        job_result["tx_hash"] = tx_hash
                        job_result["job_kind"] = f"nas_{benchmark_name}"
                        log(job_result)
                except IndexError:
                    log(f"E: Tx({tx_hash}) is reverted")


def run_job(counter) -> None:
    """Submit single job.

    :param counter: counter index to keep track of submitted job number
    """
    for idx, provider_addr in enumerate(providers):
        # yaml_cfg["config"]["data"]["data3"]["storage_id"] = random.choice(storage_ids)
        storage_id = (idx + counter) % len(storage_ids)
        selected_benchmark = random.choice(benchmarks)
        storage = storage_ids[storage_id]
        if storage == "ipfs":
            storage = random.choice(ipfs_ids)

        if selected_benchmark == "nas":
            log(f" * Submitting job from [cyan]NAS Benchmark[/cyan] to [green]{provider_addr}", "bold blue")
            yaml_cfg = Yaml(nas_yaml_fn)
            benchmark_name = create_nas_job_script()
        elif selected_benchmark == "cppr":
            log(f" * Submitting [cyan]job with cppr datasets[/cyan] to provider=[green]{provider_addr}", "bold blue")
            yaml_cfg = Yaml(cppr_yam_fn)
            log(f"data_set_idx={idx}")
            hash_medium_data_0, hash_medium_data = create_cppr_job_script(idx)
            yaml_cfg["config"]["data"]["data1"]["hash"] = hash_medium_data_0
            yaml_cfg["config"]["data"]["data2"]["hash"] = hash_medium_data
            yaml_cfg["config"]["data"]["data3"]["storage_id"] = storage
            small_datasets = Path.home() / "test_eblocbroker" / "dataset_zip" / "small"
            dirs = [d for d in os.listdir(small_datasets) if os.path.isdir(os.path.join(small_datasets, d))]
            dir_name = random.choice(dirs)
            yaml_cfg["config"]["data"]["data3"]["path"] = str(small_datasets / dir_name)

        yaml_cfg["config"]["source_code"]["storage_id"] = storage
        yaml_cfg["config"]["provider_address"] = provider_addr
        try:
            submit_base = SubmitBase(yaml_cfg.path)
            submission_date = _date()
            submission_timestamp = _timestamp()
            requester_address = random.choice(requesters).lower()
            yaml_cfg["config"]["requester_address"] = requester_address
            log(f"requester={requester_address}", "bold")
            tx_hash = submit_base.submit(is_pass=True)
            log(f"tx_hash={tx_hash}", "bold")
            tx_receipt = get_tx_status(tx_hash, is_verbose=True)
            if tx_receipt["status"] == 1:
                processed_logs = Ebb._eblocbroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
                job_result = vars(processed_logs[0].args)
                job_result["submit_date"] = submission_date
                job_result["submit_timestamp"] = submission_timestamp
                job_result["tx_hash"] = tx_hash
                if selected_benchmark == "nas":
                    job_result["job_kind"] = f"{selected_benchmark}_{benchmark_name}"
                elif selected_benchmark == "cppr":
                    job_result["job_kind"] = f"{selected_benchmark}_{hash_medium_data_0}_{hash_medium_data}"

                ebb_mongo.add_item(tx_hash, job_result)
                log(job_result)

            countdown(seconds=5, is_verbose=True)
        except Exception as e:
            print_tb(e)


def main():
    if "gdrive" in storage_ids:
        check_gdrive_user()

    console_ruler(f"NEW_TEST {Ebb.get_block_number()}")
    log(f" * {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if not is_process_on("mongod"):
        raise Exception("mongodb is not running in the background")

    counter = 0
    for _ in range(80):
        for _ in range(2):  # submitted as batch is faster
            run_job(counter)
            counter += 1

        sleep_duration = randint(250, 450)
        countdown(sleep_duration)

    log(f"#> number_of_submitted_jobs={counter}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
