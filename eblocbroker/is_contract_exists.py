#!/usr/bin/env python3

import eblocbroker.Contract as Contract

Ebb = Contract.eblocbroker


if __name__ == "__main__":
    print(f"is_contract_exists={Ebb.is_contract_exists()}")
