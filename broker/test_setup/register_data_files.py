#!/usr/bin/env python3

import time
from contextlib import suppress

from broker._utils._log import log
from broker.config import env
from broker.eblocbroker_scripts.get_data_price import get_data_price
from broker.eblocbroker_scripts.register_data import _register_data
from broker.eblocbroker_scripts.utils import Cent

hashes_small = [
    "f1de03edab51f281815c3c1e5ecb88c6",
    "03919732a417cb1d14049844b9de0f47",
    "983b9fe8a85b543dd5a4a75d031f1091",
    "b6aaf03752dc68d625fc57b451faa2bf",
    "c0fee5472f3c956ba759fd54f1fe843e",
    "63ffd1da6122e3fe9f63b1e7fcac1ff5",
    "9e8918ff9903e3314451bf2943296d31",
    "eaf488aea87a13a0bea5b83a41f3d49a",
    "e62593609805db0cd3a028194afb43b1",
    "3b0f75445e662dc87e28d60a5b13cd43",
    "ebe53bd498a9f6446cd77d9252a9847c",
    "f82aa511f8631bfc9a82fe6fa30f4b52",
    "082d2a71d86a64250f06be14c55ca27e",
    "f93b9a9f63447e0e086322b8416d4a39",
    "761691119cedfb9836a78a08742b14cc",
]

hashes_medium_1 = [
    "fe801973c5b22ef6861f2ea79dc1eb9c",  # A
    "0d6c3288ef71d89fb93734972d4eb903",  # A
    "4613abc322e8f2fdeae9a5dd10f17540",  # A
    "050e6cc8dd7e889bf7874689f1e1ead6",  # A
]

hashes_medium_2 = [
    "9d5d892a63b5758090258300a59eb389",  # B
    "779745f315060d1bc0cd44b7266fb4da",  # B
    "dd0fbccccf7a198681ab838c67b68fbf",  # B
    "45281dfec4618e5d20570812dea38760",  # B
    "bfc83d9f6d5c3d68ca09499190851e86",  # C
    "8f6faf6cfd245cae1b5feb11ae9eb3cf",  # C
    "1bfca57fe54bc46ba948023f754521d6",  # C
    "f71df9d36cd519d80a3302114779741d",  # C
]


def print_prices(hashes):
    for code_hash in hashes:
        (price, _commitment_dur) = get_data_price(env.PROVIDER_ID, code_hash, is_verbose=False)
        log(f"{code_hash}={Cent(price)._to()} usd")


def register_data_files(data_price, hashes):
    log(f"#> registering data {len(hashes)} files", h=False)
    for code_hash in hashes:
        with suppress(Exception):
            _register_data(code_hash, data_price, commitment_dur=600)
            time.sleep(1)

    print()
    time.sleep(1)


def main():
    register_data_files(data_price=Cent("0.0002 usd"), hashes=hashes_medium_1)
    register_data_files(data_price=Cent("0.0003 usd"), hashes=hashes_medium_2)
    time.sleep(2)
    try:
        print_prices(hashes_medium_1)
        print()
        print_prices(hashes_medium_2)
    except:
        log("There is no registered datafiles")

    # register_data_files(data_price=1, hashes=hashes_small)  # not required


if __name__ == "__main__":
    main()
