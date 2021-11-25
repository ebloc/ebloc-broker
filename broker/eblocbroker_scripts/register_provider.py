#!/usr/bin/env python3

import os
import sys

import ipfshttpclient

from broker import cfg
from broker._utils._log import c, log
from broker._utils.tools import print_tb
from broker._utils.web3_tools import get_tx_status
from broker._utils.yaml import Yaml
from broker.config import env
from broker.errors import QuietExit
from broker.lib import run
from broker.utils import run_ipfs_daemon

Ebb = cfg.Ebb


def _register_provider(self, *args, **kwargs):
    """Register provider."""
    if env.PROVIDER_ID == "0x0000000000000000000000000000000000000000":
        log(f"E: PROVIDER_ID={env.PROVIDER_ID} is not valid, change it in [{c.pink}]~/.ebloc-broker/.env")
        raise QuietExit

    if self.does_provider_exist(env.PROVIDER_ID):
        log(
            f"Warning: Provider {env.PROVIDER_ID} is already registered.\n"
            "Please call the [blue]update_provider_info.py[/blue] or "
            "[blue]update_provider_prices.py[/blue] script for update."
        )
        raise QuietExit

    if kwargs["commitment_blk"] < cfg.BLOCK_DURATION_1_HOUR:
        raise Exception(f"E: Commitment block number should be greater than {cfg.BLOCK_DURATION_1_HOUR}")

    if len(kwargs["federation_cloud_id"]) >= 128:
        raise Exception("E: federation_cloud_id hould be lesser than 128")

    if len(kwargs["email"]) >= 128:
        raise Exception("E: e-mail should be less than 128")

    try:
        tx = self.register_provider(*args)
        return self.tx_id(tx)
    except Exception as e:
        raise e


def get_ipfs_id() -> str:
    run_ipfs_daemon()
    try:
        client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001/http")
    except ipfshttpclient.exceptions.ConnectionError:
        log(
            "E: Failed to establish a new connection to IPFS, please run it on the background.\n"
            "Please run ~/ebloc-broker/broker/_daemons/ipfs.py"
        )
        sys.exit(1)
    except Exception as e:
        print_tb(e)
        log(
            "E: Failed to establish a new connection to IPFS, please run it on the background.\n"
            "Please run ~/ebloc-broker/broker/_daemons/ipfs.py"
        )
        sys.exit(1)

    try:
        return cfg.ipfs.get_ipfs_id(client)
    except Exception as e:
        print_tb(str(e))
        sys.exit(1)


def register_provider_wrapper(yaml_fn):
    """Register provider."""
    yaml_fn = os.path.expanduser(yaml_fn)
    if not os.path.exists(yaml_fn):
        log(f"E: yaml_fn({yaml_fn}) does not exist")
        raise QuietExit

    args = Yaml(yaml_fn)
    federation_cloud_id = args["config"]["federation_cloud_id"]
    available_core = args["config"]["available_core"]
    commitment_blk = args["config"]["commitment_blk"]
    price_core_min = args["config"]["price_core_min"]
    price_data_transfer = args["config"]["price_data_transfer"]
    price_storage = args["config"]["price_storage"]
    price_cache = args["config"]["price_cache"]
    email = args["config"]["emal"]
    args.remove_temp()
    ipfs_id = get_ipfs_id()
    gpg_fingerprint = run([env.BASH_SCRIPTS_PATH / "get_gpg_fingerprint.sh"])
    prices = [price_core_min, price_data_transfer, price_storage, price_cache]
    args = (gpg_fingerprint, email, federation_cloud_id, ipfs_id, available_core, prices, commitment_blk)
    kwargs = {
        "email": email,
        "federation_cloud_id": federation_cloud_id,
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


if __name__ == "__main__":
    yaml_fn = "/home/alper/ebloc-broker/broker/yaml_files/register_provider.yaml"
    try:
        register_provider_wrapper(yaml_fn)
    except Exception as e:
        print_tb(e)
