#!/usr/bin/env python3

import eblocbroker.Contract as Contract

ebb = Contract.eblocbroker


if __name__ == "__main__":
    print(f"is_contract_exists={ebb.is_contract_exists()}")
