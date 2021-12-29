#!/usr/bin/env python3

import os.path
import random
from pathlib import Path
from random import randint

from pymongo import MongoClient
from web3.logs import DISCARD

from broker import cfg
from broker._utils import _log
from broker._utils._log import console_ruler
from broker._utils.tools import _time, _timestamp, countdown, log, run
from broker._utils.web3_tools import get_tx_status
from broker._utils.yaml import Yaml
from broker.libs.mongodb import BaseMongoClass
from broker.submit_base import SubmitBase
from broker.test_setup._users import users
from broker.utils import print_tb

yaml_files = ["job_nas.yaml"]
Ebb = cfg.Ebb
cfg.IS_TEST = True

_log.ll.LOG_FILENAME = Path.home() / ".ebloc-broker" / "test.log"

provider_addresses = [
    "0x3e6FfC5EdE9ee6d782303B2dc5f13AFeEE277AeA",
    "0x765508fc8f78a465f518ae79897d0e4b249e82dc",
    "0x38cc03c7e2a7d2acce50045141633ecdcf477e9a",
    "0xeab50158e8e51de21616307a99c9604c1c453a02",
]


def create_cppr_job_script():
    """Create cppr slurm job script to be submitted."""
    registered_data_hashes_small = [
        "b6aaf03752dc68d625fc57b451faa2bf",
        "f1de03edab51f281815c3c1e5ecb88c6",
        "082d2a71d86a64250f06be14c55ca27e",
        "03919732a417cb1d14049844b9de0f47",
        "983b9fe8a85b543dd5a4a75d031f1091",
        "f71df9d36cd519d80a3302114779741d",
        "c0fee5472f3c956ba759fd54f1fe843e",
        "63ffd1da6122e3fe9f63b1e7fcac1ff5",
        "9e8918ff9903e3314451bf2943296d31",
        "eaf488aea87a13a0bea5b83a41f3d49a",
        "e62593609805db0cd3a028194afb43b1",
        "3b0f75445e662dc87e28d60a5b13cd43",
        "ebe53bd498a9f6446cd77d9252a9847c",
        "f82aa511f8631bfc9a82fe6fa30f4b52",
        "761691119cedfb9836a78a08742b14cc",
        "f93b9a9f63447e0e086322b8416d4a39",
    ]

    registered_data_hashes_medium = [
        "050e6cc8dd7e889bf7874689f1e1ead6",
        "9d5d892a63b5758090258300a59eb389",
        "779745f315060d1bc0cd44b7266fb4da",
        "fe801973c5b22ef6861f2ea79dc1eb9c",
        "0d6c3288ef71d89fb93734972d4eb903",
        "4613abc322e8f2fdeae9a5dd10f17540",
        "dd0fbccccf7a198681ab838c67b68fbf",
        "45281dfec4618e5d20570812dea38760",
        "fa64e96bcee96dbc480a1495bddbf53c",
        "8f6faf6cfd245cae1b5feb11ae9eb3cf",
        "1bfca57fe54bc46ba948023f754521d6",
    ]

    hash_small_data = random.choice(registered_data_hashes_small)
    hash_med_data = random.choice(registered_data_hashes_medium)
    fn = Path.home() / "test_eblocbroker" / "run_cppr" / "run.sh"
    f = open(fn, "w+")
    f.write("#!/bin/bash\n")
    f.write("#SBATCH -o slurm.out  # STDOUT\n")
    f.write("#SBATCH -e slurm.err  # STDERR\n")
    f.write("#SBATCH --mail-type=ALL\n\n")
    f.write("export OMP_NUM_THREADS=1\n")
    f.write("current_date=$(LANG=en_us_88591; date)\n")
    f.write(f"DATA_HASH='{hash_small_data}'\n")
    f.write("DATA1_DIR='../data_link/'$DATA_HASH'/'\n")
    f.write("echo ' * '$current_date > output.log\n")
    f.write("find $DATA1_DIR -name '*.max' -print0 | while read -d $'\\0' file\n")
    f.write("do\n")
    f.write("    echo $file >> output.log\n")
    f.write("    (/usr/bin/time -v cppr -a pr $file) >> output.log 2>&1\n")
    f.write("done\n")
    f.write(f"DATA_HASH='{hash_med_data}'\n")
    f.write("DATA2_DIR='../data_link/'$DATA_HASH'/'\n")
    f.write("echo ' * '$current_date >> output.log\n")
    f.write("find $DATA2_DIR -name '*.max' -print0 | while read -d $'\\0' file\n")
    f.write("do\n")
    f.write("    echo $file >> output.log\n")
    f.write("    (/usr/bin/time -v cppr -a pr $file) >> output.log 2>&1\n")
    f.write("done\n")
    #
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
    return hash_small_data, hash_med_data


def create_nas_job_script(is_small=False):
    """Create NPB3.3-SER slurm job script to be submitted."""
    benchmark_names = ["bt", "cg", "ep", "is", "lu", "sp", "ua"]
    benchmark_name = random.choice(benchmark_names)
    output_fn = "output.log"
    hash_str = random.getrandbits(128)
    fn = Path.home() / "test_eblocbroker" / "NPB3.3-SER_source_code" / "run.sh"
    f = open(fn, "w+")
    f.write("#!/bin/bash\n")
    f.write("#SBATCH -o slurm.out  # STDOUT\n")
    f.write("#SBATCH -e slurm.err  # STDERR\n")
    f.write("#SBATCH --mail-type=ALL\n\n")
    f.write(f"make {benchmark_name} CLASS=A > {output_fn}\n")
    f.write(f"/usr/bin/time -v bin/{benchmark_name}.A.x >> {output_fn}\n")
    if not is_small:
        f.write(f"make {benchmark_name} CLASS=B >> {output_fn}\n")
        f.write(f"/usr/bin/time -v bin/{benchmark_name}.B.x >> {output_fn}\n")
        f.write(f"make {benchmark_name} CLASS=C >> {output_fn}\n")
        f.write(f"/usr/bin/time -v bin/{benchmark_name}.C.x >> {output_fn}\n")

    f.write(f"# {hash_str}\n")
    f.close()
    run(["sed", "-i", r"s/\x0//g", fn])  # remove NULL characters from the SBATCH file
    return benchmark_name


def pre_submit(storage_ids, provider_address):
    is_pass = True
    required_confs = 0
    yaml_fn = Path.home() / "ebloc-broker" / "broker" / "test_setup" / "nas" / "job_nas.yaml"
    yaml_cfg = Yaml(yaml_fn)
    yaml_cfg["config"]["provider_address"] = provider_address
    for storage_id in storage_ids:
        yaml_cfg["config"]["source_code"]["storage_id"] = storage_id
        benchmark_name = create_nas_job_script(is_small=True)
        submit_base = SubmitBase(yaml_cfg.path)
        tx_hash = submit_base.submit(is_pass, required_confs)
        if required_confs >= 1:
            tx_receipt = get_tx_status(tx_hash, is_silent=True)
            if tx_receipt["status"] == 1:
                processed_logs = Ebb._eBlocBroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
                try:
                    if processed_logs:
                        job_result = vars(processed_logs[0].args)
                        job_result["tx_hash"] = tx_hash
                        job_result["submitted_job_kind"] = f"nas_{benchmark_name}"
                        log(job_result)
                except IndexError:
                    log(f"E: Tx({tx_hash}) is reverted")

        # breakpoint()  # DEBUG


def main():
    console_ruler(f"NEW_TEST {Ebb.get_block_number()}")
    mc = MongoClient()
    ebb_mongo = BaseMongoClass(mc, mc["ebloc_broker"]["tests"])
    storage_ids = ["eudat", "gdrive", "ipfs"]
    ipfs_ids = ["ipfs_gpg", "ipfs"]
    # for provider_address in provider_addresses:
    #     pre_submit(storage_ids, provider_address)

    benchmarks = ["nas", "cppr"]
    test_dir = Path.home() / "ebloc-broker" / "broker" / "test_setup" / "nas"
    nas_yaml_fn = test_dir / "job_nas.yaml"
    cppr_yam_fn = test_dir / "job_cppr.yaml"
    counter = 0
    yaml_cfg = None
    # storage = None
    for _ in range(50):
        for _ in range(2):  # submitted as batch is faster
            for idx, provider_address in enumerate(provider_addresses):
                # yaml_cfg["config"]["data"]["data3"]["storage_id"] = random.choice(storage_ids)
                storage_id = (idx + counter) % len(storage_ids)
                selected_benchmark = random.choice(benchmarks)
                storage = storage_ids[storage_id]
                if storage == "ipfs":
                    storage = random.choice(ipfs_ids)

                if selected_benchmark == "nas":
                    log(f" * Submitting job from NAS Benchmark to [green]{provider_address}", "bold blue")
                    yaml_cfg = Yaml(nas_yaml_fn)
                    benchmark_name = create_nas_job_script()
                elif selected_benchmark == "cppr":
                    log(f" * Submitting job with cppr datasets to [green]{provider_address}", "bold blue")
                    yaml_cfg = Yaml(cppr_yam_fn)
                    hash_small_data, hash_med_data = create_cppr_job_script()
                    yaml_cfg["config"]["data"]["data1"]["hash"] = hash_small_data
                    yaml_cfg["config"]["data"]["data2"]["hash"] = hash_med_data
                    yaml_cfg["config"]["data"]["data3"]["storage_id"] = storage
                    small_datasets = Path.home() / "test_eblocbroker" / "dataset_zip" / "small"
                    dirs = [d for d in os.listdir(small_datasets) if os.path.isdir(os.path.join(small_datasets, d))]
                    dir_name = random.choice(dirs)
                    yaml_cfg["config"]["data"]["data3"]["path"] = str(small_datasets / dir_name)

                yaml_cfg["config"]["source_code"]["storage_id"] = storage
                yaml_cfg["config"]["provider_address"] = provider_address
                try:
                    submit_base = SubmitBase(yaml_cfg.path)
                    submission_date = _time()
                    submission_timestamp = _timestamp()
                    requester_address = random.choice(users).lower()
                    yaml_cfg["config"]["requester_address"] = requester_address
                    log(f"requester={requester_address}", "bold")
                    tx_hash = submit_base.submit(is_pass=True)
                    log(f"tx_hash={tx_hash}", "bold")
                    tx_receipt = get_tx_status(tx_hash, is_silent=True)
                    if tx_receipt["status"] == 1:
                        processed_logs = Ebb._eBlocBroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
                        job_result = vars(processed_logs[0].args)
                        job_result["submit_date"] = submission_date
                        job_result["submit_timestamp"] = submission_timestamp
                        job_result["tx_hash"] = tx_hash
                        if selected_benchmark == "nas":
                            job_result["submitted_job_kind"] = f"{selected_benchmark}_{benchmark_name}"
                        elif selected_benchmark == "cppr":
                            job_result["submitted_job_kind"] = f"{selected_benchmark}_{hash_small_data}_{hash_med_data}"

                        ebb_mongo.add_item(tx_hash, job_result)
                        log(job_result)

                    countdown(seconds=5, is_silent=True)
                except Exception as e:
                    print_tb(e)

            counter += 1
        sleep_time = randint(300, 500)
        countdown(sleep_time)


if __name__ == "__main__":
    main()
