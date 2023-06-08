#!/usr/bin/env python3

import csv

from broker import cfg
from broker._utils._log import log
from broker._utils.tools import print_tb
from broker.errors import QuietExit

Ebb = cfg.Ebb


def main():
    submitJob_gas_used = {}
    submitJob_gas_used["cppr"] = 0
    submitJob_gas_used["nas"] = 0

    elapsed_time = {}
    elapsed_time_count = {}
    completion_time = {}

    processPayment_gas_used = {}
    processPayment_gas_used["cppr"] = 0
    processPayment_gas_used["nas"] = 0
    count_nas = 0
    count_cppr = 0
    wait_time = {}
    fn = "/Users/alper/junk/p1.csv"
    with open(fn) as f:
        reader = csv.reader(f, delimiter="\t", skipinitialspace=True)
        for idx, line in enumerate(reader):
            if idx == 0:
                for i, item in enumerate(line):
                    print(f"{i} => {item}")
            else:
                key = line[2]
                workload = line[4]
                _type = None
                if key[:2] == "Qm":
                    _type = "ipfs"
                elif len(key) == 32:
                    _type = "eudat"
                else:
                    _type = "gdrive"

                k = f"{workload}_{_type}"
                k_elapsed = f"{line[0]}_{workload}"
                if k_elapsed not in elapsed_time:
                    elapsed_time[k_elapsed] = 0
                    elapsed_time_count[k_elapsed] = 0

                if k_elapsed not in completion_time:
                    completion_time[k_elapsed] = 0

                if k not in wait_time:
                    wait_time[k] = 0

                if line[5] == "COMPLETED":
                    # log(f"({idx},{line[18]})")
                    elapsed_time[k_elapsed] += int(line[11])
                    elapsed_time_count[k_elapsed] += 1
                    #
                    a = Ebb.get_block(int(line[7]))["timestamp"]
                    b = Ebb.get_block(int(line[len(line) - 1]))["timestamp"]

                    completion_time[k_elapsed] += float(format(float((b - a) / 60), ".2f"))

                    wait_time[k] += int(line[10])
                    submitJob_gas_used[workload] += int(line[len(line) - 4])
                    processPayment_gas_used[workload] += int(line[len(line) - 2])
                    if workload == "nas":
                        count_nas += 1
                    else:
                        count_cppr += 1

    log(wait_time)

    log(int(submitJob_gas_used["nas"] / count_nas))
    log(int(processPayment_gas_used["nas"] / count_nas))

    log(int(submitJob_gas_used["cppr"] / count_nas))
    log(int(processPayment_gas_used["cppr"] / count_nas))

    log(submitJob_gas_used)
    log(processPayment_gas_used)
    log(count_nas)
    log(count_cppr)
    ##########
    for k, v in elapsed_time.items():
        if k != "_workload":
            print(k, v / elapsed_time_count[k])

    print("~~~~~~~~~~~~~~~~~~")
    for k, v in completion_time.items():
        if k != "_workload":
            print(k, v / elapsed_time_count[k])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"#> {e}")
    except Exception as e:
        print_tb(str(e))
