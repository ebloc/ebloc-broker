#!/usr/bin/env python3

from broker import cfg
from broker.utils import log

Ebb = cfg.Ebb


def get_data_price(provider, source_code_hash):
    code_hash_bytes = cfg.w3.toBytes(text=source_code_hash)
    data_block_numbers = Ebb.get_registered_data_bn(provider, code_hash_bytes)
    (price, commitment_block_duration) = Ebb.get_registered_data_price(
        provider, code_hash_bytes, data_block_numbers[-1]
    )
    log(f"==> price={price}")
    log(f"==> commitment_block_duration={commitment_block_duration}")
    log(f"==> data_block_numbers={data_block_numbers}")


def main():
    address = "0x29e613b04125c16db3f3613563bfdd0ba24cb629"
    code_hash = "9d5d892a63b5758090258300a59eb389"
    get_data_price(address, code_hash)


if __name__ == "__main__":
    main()
