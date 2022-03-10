#!/usr/bin/env python3

import os
import re
import sys
from os.path import expanduser

import ipfshttpclient

from broker import cfg
from broker._utils._log import c, log
from broker._utils.tools import get_gpg_fingerprint, get_ip, is_byte_str_zero, is_gpg_published, print_tb
from broker._utils.web3_tools import get_tx_status
from broker._utils.yaml import Yaml
from broker.config import env
from broker.errors import QuietExit
from broker.utils import run_ipfs_daemon

Ebb = cfg.Ebb


def _register_provider(self, *args, **kwargs):
    """Register provider."""
    if is_byte_str_zero(env.PROVIDER_ID):
        log(f"E: PROVIDER_ID={env.PROVIDER_ID} is not valid, change it in [{c.pink}]~/.ebloc-broker/.env")
        raise QuietExit

    if self.does_provider_exist(env.PROVIDER_ID):
        log(
            f"warning: Provider {env.PROVIDER_ID} is already registered.\n"
            "Please call the [blue]update_provider_info.py[/blue] or "
            "[blue]update_provider_prices.py[/blue] script for an update."
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
        # may create error
        client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001/http")
    except ipfshttpclient.exceptions.ConnectionError:
        log(
            "E: Failed to establish a new connection to IPFS, please run it on the background.\n"
            "Please run [magenta]~/ebloc-broker/broker/_daemons/ipfs.py"
        )
        sys.exit(1)
    except Exception as e:
        print_tb(e)
        log(
            "E: Failed to establish a new connection to IPFS, please run it on the background.\n"
            "Please run [magenta]~/ebloc-broker/broker/_daemons/ipfs.py"
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
    # @b2drop.eudat.eu

    federation_cloud_id = args["cfg"]["oc_user"]
    email = args["cfg"]["gmail"]
    available_core = args["cfg"]["provider"]["available_core"]
    commitment_blk = args["cfg"]["provider"]["prices"]["commitment_blk"]
    price_core_min = args["cfg"]["provider"]["prices"]["price_core_min"]
    price_data_transfer = args["cfg"]["provider"]["prices"]["price_data_transfer"]
    price_storage = args["cfg"]["provider"]["prices"]["price_storage"]
    price_cache = args["cfg"]["provider"]["prices"]["price_cache"]
    exit_flag = False

    if not federation_cloud_id:
        log(f"E: [blue]federation_cloud_id[/blue] is empty in [magenta]{yaml_fn}")
        exit_flag = True

    if not available_core:
        log(f"E: [blue]available_core[/blue] is empty in [magenta]{yaml_fn}")
        exit_flag = True

    if not commitment_blk:
        log(f"E: [blue]commitment_blk[/blue] is empty in [magenta]{yaml_fn}")
        exit_flag = True

    if not price_core_min:
        log(f"E: [blue]price_core_min[/blue] is empty in [magenta]{yaml_fn}")
        exit_flag = True

    if not price_data_transfer:
        log(f"E: [blue]price_data_transfer[/blue] is empty in [magenta]{yaml_fn}")
        exit_flag = True

    if not price_storage:
        log(f"E: [blue]price_storage[/blue] is empty in [magenta]{yaml_fn}")
        exit_flag = True

    if not price_cache:
        log(f"E: [blue]price_cache[/blue] is empty in [magenta]{yaml_fn}")
        exit_flag = True

    if not email:
        log(f"E: [blue]email[/blue] is empty in [magenta]{yaml_fn}")
        exit_flag = True

    if exit_flag:
        sys.exit(1)

    ipfs_id = get_ipfs_id()
    ip_address = get_ip()
    if ip_address not in ipfs_id:
        # public IP should exists in the ipfs id
        ipfs_address = re.sub("ip4.*?tcp", f"ip4/{ip_address}/tcp", ipfs_id, flags=re.DOTALL)
        log(f"==> ipfs_address={ipfs_address}")
    else:
        ipfs_address = ipfs_id

    try:
        email = env.GMAIL
        gpg_fingerprint = get_gpg_fingerprint(email)
        is_gpg_published(gpg_fingerprint)
    except Exception as e:
        raise e

    if not email:
        log("E: Please provide a valid e-mail")
        sys.exit(1)

    prices = [price_core_min, price_data_transfer, price_storage, price_cache]
    args = (gpg_fingerprint, email, federation_cloud_id, ipfs_address, available_core, prices, commitment_blk)
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
    try:
        # yaml_fn = expanduser("~/ebloc-broker/broker/yaml_files/register_provider.yaml")
        yaml_fn = expanduser("~/.ebloc-broker/cfg.yaml")  # setup for the provider
        register_provider_wrapper(yaml_fn)
    except Exception as e:
        print_tb(e)
