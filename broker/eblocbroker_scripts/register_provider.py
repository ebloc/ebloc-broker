#!/usr/bin/env python3

import ipfshttpclient
import os
import re
import sys
from os.path import expanduser
import socket
from broker import cfg
from broker._utils._log import log
from broker._utils.tools import get_ip, is_byte_str_zero, print_tb
from broker._utils.web3_tools import get_tx_status
from broker._utils.yaml import Yaml
from broker.config import env
from broker.eblocbroker_scripts.utils import Cent
from broker.errors import QuietExit
from broker.utils import start_ipfs_daemon

Ebb = cfg.Ebb
ipfs = cfg.ipfs


def _register_provider(self, *args, **kwargs):
    """Register provider."""
    if is_byte_str_zero(env.PROVIDER_ID):
        log(f"E: PROVIDER_ID={env.PROVIDER_ID} is not valid, change it in [m]~/.ebloc-broker/cfg.yaml")
        raise QuietExit

    if self.does_provider_exist(env.PROVIDER_ID):
        log(
            f"warning: Provider {env.PROVIDER_ID} is already registered.\n"
            "Please call the [blue]update_provider_info.py[/blue] or "
            "[blue]update_provider_prices.py[/blue] script for an update."
        )
        raise QuietExit

    if kwargs["commitment_blk"] < cfg.ONE_HOUR_BLOCK_DURATION:
        raise Exception(f"Commitment block number should be greater than {cfg.ONE_HOUR_BLOCK_DURATION}")

    if len(kwargs["f_id"]) >= 128:
        raise Exception("f_id hould be lesser than 128")

    if len(kwargs["gmail"]) >= 128:
        raise Exception("e-mail should be less than 128")

    try:
        tx = self.register_provider(*args)
        return self.tx_id(tx)
    except Exception as e:
        raise e


def get_ipfs_address() -> str:
    start_ipfs_daemon()
    if ipfs.client:
        return ipfs.get_ipfs_address()
    else:
        try:
            # may create error
            client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001/http")
        except ipfshttpclient.exceptions.ConnectionError:
            log(
                "E: Failed to establish a new connection to IPFS, please run it on the background.\n"
                "Please run [m]~/ebloc-broker/broker/_daemons/ipfs.py"
            )
            sys.exit(1)
        except Exception as e:
            print_tb(e)
            log(
                "E: Failed to establish a new connection to IPFS, please run it on the background.\n"
                "Please run [m]~/ebloc-broker/broker/_daemons/ipfs.py"
            )
            sys.exit(1)

        try:
            return ipfs.get_ipfs_address(client)
        except Exception as e:
            print_tb(str(e))
            sys.exit(1)


def register_provider_wrapper(yaml_fn):
    """Register provider."""
    yaml_fn = expanduser(yaml_fn)
    if not os.path.exists(yaml_fn):
        log(f"E: yaml_fn({yaml_fn}) does not exist")
        raise QuietExit

    args = Yaml(yaml_fn, auto_dump=False)
    f_id = args["cfg"]["oc_username"].replace("@b2drop.eudat.eu", "")
    gmail = args["cfg"]["gmail"]
    _args = args["cfg"]["provider"]
    available_core = _args["available_core"]
    _prices = _args["prices"]
    commitment_blk = _prices["commitment_blk"]
    try:
        price_core_min = Cent(_prices["price_core_min"])
        price_data_transfer = Cent(_prices["price_data_transfer"])
        price_storage = Cent(_prices["price_storage"])
        price_cache = Cent(_prices["price_cache"])
    except Exception as e:
        print_tb(e)

    exit_flag = False
    if env.PROVIDER_ID == Ebb.get_owner():
        log("E: Address cannot be same as owner's")
        exit_flag = True

    error_list = []
    if not f_id:
        error_list.append("f_id")
        exit_flag = True

    if not available_core:
        error_list.append("available_core")
        exit_flag = True

    if not commitment_blk:
        error_list.append("commitment_blk")
        exit_flag = True

    if not price_core_min:
        error_list.append("price_core_min")
        exit_flag = True

    if not price_data_transfer:
        error_list.append("price_data_transfer")
        exit_flag = True

    if not price_storage:
        error_list.append("price_storage")
        exit_flag = True

    if not price_cache:
        error_list.append("price_cache")
        exit_flag = True

    if not gmail:
        error_list.append("gmail")
        exit_flag = True

    if exit_flag:
        if len(error_list) == 1:
            log(f"E: [blue]{error_list[0]}[/blue] is empty in [m]{yaml_fn}")
        else:
            log(f"E: [blue]{error_list}[/blue] variables are empty in [m]{yaml_fn}")

        sys.exit(1)

    ipfs_address = get_ipfs_address()
    ip = get_ip()
    if ip not in ipfs_address:
        # public IP should exists in the ipfs id
        ipfs_address = re.sub("ip4.*?tcp", f"ip4/{ip}/tcp", ipfs_address, flags=re.DOTALL)
        log(f"==> ipfs_address={ipfs_address}")

    gmail = env.GMAIL
    try:
        gpg_fingerprint = ipfs.get_gpg_fingerprint(gmail)
        ipfs.is_gpg_published(gpg_fingerprint)
        ipfs.publish_gpg(gpg_fingerprint)
    except Exception as e:
        raise e

    if not gmail:
        log("E: Please provide a valid e-mail")
        sys.exit(1)

    prices = [price_core_min, price_data_transfer, price_storage, price_cache]
    args = (gpg_fingerprint, gmail, f_id, ipfs_address, available_core, prices, commitment_blk)
    kwargs = {
        "gmail": gmail,
        "f_id": f_id,
        "commitment_blk": commitment_blk,
    }
    try:
        tx_hash = Ebb._register_provider(*args, **kwargs)
        if tx_hash:
            get_tx_status(tx_hash)
        else:
            log()
    except QuietExit:
        pass
    except Exception as e:
        raise e


def main():
    try:
        # yaml_fn = expanduser("~/ebloc-broker/broker/yaml_files/register_provider.yaml")
        yaml_fn = expanduser("~/.ebloc-broker/cfg.yaml")  # setup for the provider
        register_provider_wrapper(yaml_fn)
    except Exception as e:
        print_tb(e)


if __name__ == "__main__":
    main()
