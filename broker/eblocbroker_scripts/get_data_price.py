#!/usr/bin/env python3

from broker import cfg
from broker.utils import log

Ebb = cfg.Ebb


def get_data_price(provider, source_code_hash, is_verbose=True):
    bn = Ebb.get_block_number()
    note_msg = ""
    if isinstance(source_code_hash, bytes):
        code_hash_bytes = source_code_hash
    else:
        code_hash_bytes = cfg.w3.toBytes(text=source_code_hash)

    registered_data_bn_list = Ebb.get_registered_data_bn(provider, code_hash_bytes)
    if bn > registered_data_bn_list[-1]:
        data_fee_set_bn = registered_data_bn_list[-1]
    else:
        data_fee_set_bn = registered_data_bn_list[-2]
        if is_verbose:
            remaining_min = (registered_data_bn_list[-1] - bn) * 6 / 60
            note_msg = f"{remaining_min} minutes remaining for new price to take place"

    (price, commitment_block_dur) = Ebb.get_registered_data_price(provider, code_hash_bytes, data_fee_set_bn)
    if is_verbose:
        log(f" * price={price}")
        log(f" * commitment_block_dur={commitment_block_dur}")

        prices = []
        for _bn in registered_data_bn_list:
            (price, commitment_block_dur) = Ebb.get_registered_data_price(provider, code_hash_bytes, _bn)
            prices.append(price)

        log(f" * registered_data_bn_list={registered_data_bn_list}")
        log(f" *                  prices={prices}")
        if note_msg:
            log(f"## {note_msg}")

    return price, commitment_block_dur


def get_latest_data_price(provider, source_code_hash, is_verbose=True):
    if isinstance(source_code_hash, bytes):
        code_hash_bytes = source_code_hash
    else:
        code_hash_bytes = cfg.w3.toBytes(text=source_code_hash)

    registered_data_bn_list = Ebb.get_registered_data_bn(provider, code_hash_bytes)
    (price, commitment_block_dur) = Ebb.get_registered_data_price(
        provider, code_hash_bytes, registered_data_bn_list[-1]
    )
    if is_verbose:
        log(f" * price={price}")
        log(f" * commitment_block_dur={commitment_block_dur}")
        log(f" * registered_data_bn_list={registered_data_bn_list}")

    return price, commitment_block_dur


def main():
    provider_address = "0x29e613b04125c16db3f3613563bfdd0ba24cb629"
    code_hash = "050e6cc8dd7e889bf7874689f1e1ead6"
    get_data_price(provider_address, code_hash)


if __name__ == "__main__":
    main()
