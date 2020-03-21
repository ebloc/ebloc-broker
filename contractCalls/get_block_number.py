#!/usr/bin/env python3

import sys

import config
from config import load_log
from imports import connect_to_web3

logging = load_log()


def get_block_number():
    if config.w3 is None:
        config.w3 = connect_to_web3()
        if not config.w3:
            raise Exception("web3 is not connected")

    return config.w3.eth.blockNumber


if __name__ == "__main__":
    is_write_to_file = False
    if len(sys.argv) == 2:
        is_write_to_file = sys.argv[1]
        if is_write_to_file == "1" or is_write_to_file == "True":
            is_write_to_file = True

    try:
        output = get_block_number()
        if is_write_to_file:
            print(output)
        else:
            logging.info(f"block_number={output}")
    except Exception as error:
        if not is_write_to_file:
            logging.error(f"E: {str(error)}")

    exit(0)
