#!/usr/bin/env python3

import sys

import broker.cfg as cfg

if __name__ == "__main__":
    Ebb = cfg.Ebb
    if len(sys.argv) == 3:
        provider_addr = str(sys.argv[1])
        source_code_hash = str(sys.argv[2])
    else:
        provider_addr = "0x57b60037b82154ec7149142c606ba024fbb0f991"
        source_code_hash = "acfd2fd8a1e9ccf031db0a93a861f6eb"

    received_block_num, storage_time = Ebb.getJobStorageTime(provider_addr, source_code_hash)
    print(
        f"received_block_num={received_block_num}; storage_time={storage_time};"
        f" endBlockTime={received_block_num + storage_time * 240}"
    )
