#!/usr/bin/env python3

from broker import cfg
from broker.utils import log


def get_data_price(provider, source_code_hash):
    code_hash_bytes = cfg.w3.toBytes(text=source_code_hash)
    (price, commitment_block_duration) = cfg.Ebb.get_registered_data_prices(provider, code_hash_bytes, 0)
    log(f"==> price={price}")
    log(f"==> commitment_block_duration={commitment_block_duration}")


if __name__ == "__main__":
    address = "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49"
    code_hash = "b6aaf03752dc68d625fc57b451faa2bf"
    get_data_price(address, code_hash)
