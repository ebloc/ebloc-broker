#!/usr/bin/env python3

from broker import cfg
from broker.utils import log


def get_data_price(provider, source_code_hash):
    source_code_hash_bytes = cfg.w3.toBytes(text=source_code_hash)
    (price, _commitment_block_duration) = cfg.Ebb.get_registered_data_prices(provider, source_code_hash_bytes, 0)
    log(f"==> price={price}")
    log(f"==> commitment_block_duration={_commitment_block_duration}")


if __name__ == "__main__":
    get_data_price("0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49", "b6aaf03752dc68d625fc57b451faa2bf")
