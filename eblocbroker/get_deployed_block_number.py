#!/usr/bin/env python3

import eblocbroker.Contract as Contract

ebb = Contract.eblocbroker

if __name__ == "__main__":
    print(ebb.get_deployed_block_number())
