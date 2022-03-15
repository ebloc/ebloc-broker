#!/usr/bin/env python3

import sys

from broker import cfg


def main():
    Ebb = cfg.Ebb
    if len(sys.argv) == 3:
        provider_addr = str(sys.argv[1])
        source_code_hash = str(sys.argv[2])
    else:
        provider_addr = "0x57b60037b82154ec7149142c606ba024fbb0f991"
        source_code_hash = "acfd2fd8a1e9ccf031db0a93a861f6eb"

    received_block_num, storage_duration = Ebb.getStorageInfo(provider_addr, source_code_hash)
    print(
        f"received_block_num={received_block_num}; storage_duration={storage_duration};"
        f" end_block_time={received_block_num + storage_duration * cfg.BLOCK_DURATION_1_HOUR}"
    )


if __name__ == "__main__":
    main()
