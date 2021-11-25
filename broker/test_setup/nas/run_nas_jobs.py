#!/usr/bin/env python3

import random
from pathlib import Path
from random import randint

from web3.logs import DISCARD

from broker import cfg
from broker._utils.tools import countdown, log
from broker._utils.web3_tools import get_tx_status
from broker._utils.yaml import Yaml
from broker.submit_base import SubmitBase


def create_nas_run():
    benchmark_names = ["bt", "cg", "ep", "is", "lu", "sp", "ua"]
    benchmark_name = random.choice(benchmark_names)
    fn = Path.home() / "test_eblocbroker" / "NPB3.3-SER_source_code" / "run.sh"
    f = open(fn, "w+")
    f.write("#!/bin/bash\n")
    f.write("#SBATCH -o slurm.out  # STDOUT\n")
    f.write("#SBATCH -e slurm.err  # STDERR\n")
    f.write("#SBATCH --mail-type=ALL\n\n")
    f.write(f"make {benchmark_name} CLASS=A > output.txt\n")
    f.write(f"/usr/bin/time -v bin/{benchmark_name}.A.x >> output.txt\n")
    f.write(f"make {benchmark_name} CLASS=B >> output.txt\n")
    f.write(f"/usr/bin/time -v bin/{benchmark_name}.B.x >> output.txt\n")
    f.write(f"make {benchmark_name} CLASS=C >> output.txt\n")
    f.write(f"/usr/bin/time -v bin/{benchmark_name}.C.x >> output.txt\n")
    f.close()


def main():
    storage_ids = ["ipfs", "eudat", "gdrive"]  # "ipfs_gpg"
    Ebb = cfg.Ebb
    for _ in range(25):
        for _ in range(3):  # submitted as batch is faster
            yaml_fn = Path.home() / "ebloc-broker" / "broker" / "test_setup" / "nas" / "job.yaml"
            yaml_cfg = Yaml(yaml_fn)
            _storage_id = random.choice(storage_ids)
            _storage_id = "gdrive"
            yaml_cfg["config"]["source_code"]["storage_id"] = _storage_id
            submit_base = SubmitBase(yaml_fn)
            create_nas_run()
            tx_hash = submit_base.submit()
            results = {}
            log(f"tx_hash={tx_hash}", "bold")
            tx_receipt = get_tx_status(tx_hash, is_silent=True)
            if tx_receipt["status"] == 1:
                processed_logs = Ebb._eBlocBroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
                log(vars(processed_logs[0].args))

        sleep_time = randint(600, 900)
        countdown(sleep_time)


if __name__ == "__main__":
    main()


# hashesFile.write(
#     tarHash
#     + " "
#     + str(coreLimit)
#     + " "
#     + str(coreNum)
#     + " "
#     + str(startTime)
#     + " "
#     + str(startTime + coreLimit)
#     + " "
#     + tarHash
#     + " "
#     + str(sleepTime)
#     + "\n"
# )
# startTime += sleepTime
