#!/usr/bin/env python3

import os
import sys

import ipfshttpclient

from broker import cfg
from broker._utils._log import c, log
from broker._utils.tools import is_byte_str_zero, is_gpg_published, print_tb
from broker._utils.web3_tools import get_tx_status
from broker._utils.yaml import Yaml
from broker.config import env
from broker.errors import QuietExit
from broker.lib import run
from broker.utils import question_yes_no, run_ipfs_daemon

Ebb = cfg.Ebb


def register_requester(self, yaml_fn):
    """Register or update requester into smart contract."""
    yaml_fn = os.path.expanduser(yaml_fn)
    try:
        run_ipfs_daemon()
        client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001/http")
    except Exception as e:
        log("E: Run ipfs daemon to detect your ipfs_id")
        print_tb(e)
        sys.exit(1)

    if not os.path.exists(yaml_fn):
        log(f"E: yaml_fn({yaml_fn}) does not exist")
        raise QuietExit

    args = Yaml(yaml_fn)
    ipfs_id = cfg.ipfs.get_ipfs_id(client)
    gpg_fingerprint = run([env.BASH_SCRIPTS_PATH / "get_gpg_fingerprint.sh"])
    try:
        is_gpg_published(gpg_fingerprint)
    except Exception as e:
        raise e

    account = args["config"]["account"]
    email = args["config"]["email"]
    federation_cloud_id = args["config"]["federation_cloud_id"]
    args.remove_temp()
    # if env.IS_BLOXBERG:
    #     account = self.brownie_load_account().address

    log(f"==> registering {account} as requester")
    if is_byte_str_zero(account):
        log(f"E: account={account} is not valid, change it in [{c.pink}]~/.ebloc-broker/.env")
        raise QuietExit

    if len(federation_cloud_id) >= 128:
        raise Exception("E: federation_cloud_id is more than 128")

    if len(email) >= 128:
        raise Exception("E: email is more than 128")

    if len(gpg_fingerprint) != 40:
        raise Exception("E: gpg_fingerprint should be 40 characters")

    if self.does_requester_exist(account):
        log(f"warning: Requester {account} is already registered")
        requester_info = Ebb.get_requester_info(account)
        if (
            requester_info["email"] == email
            and requester_info["gpg_fingerprint"] == gpg_fingerprint.lower()
            and requester_info["ipfs_id"] == ipfs_id
            and requester_info["f_id"] == federation_cloud_id
        ):
            log("## Same requester information is provided, nothing to do")
            raise QuietExit

        requester_info = {
            "email": email,
            "federation_cloud_id": federation_cloud_id,
            "gpg_fingerprint": gpg_fingerprint,
            "ipfs_id": ipfs_id,
        }
        log("==> [bold yellow]new_requester_info:")
        log(requester_info)
        if not question_yes_no("#> Would you like to update provider info?"):
            return

    try:
        tx = self._register_requester(account, gpg_fingerprint, email, federation_cloud_id, ipfs_id)
        return self.tx_id(tx)
    except Exception as e:
        print_tb(e)
        raise e


if __name__ == "__main__":
    try:
        yaml_fn = "~/ebloc-broker/broker/yaml_files/register_requester.yaml"
        tx_hash = Ebb.register_requester(yaml_fn)
        if tx_hash:
            get_tx_status(tx_hash)
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)
