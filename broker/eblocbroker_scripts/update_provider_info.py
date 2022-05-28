#!/usr/bin/env python3

import re

from broker import cfg
from broker._utils.tools import get_ip, log, print_tb
from broker._utils.web3_tools import get_tx_status
from broker.config import env
from broker.eblocbroker_scripts.register_provider import get_ipfs_id
from broker.errors import QuietExit


def is_provider_info_match(self, gmail, ipfs_id, gpg_fingerprint, f_id):
    try:
        provider_info = self.get_provider_info(env.PROVIDER_ID)
        if (
            provider_info["gpg_fingerprint"] == gpg_fingerprint.upper()
            and provider_info["gmail"] == gmail
            and provider_info["f_id"] == f_id
            and provider_info["ipfs_id"] == ipfs_id
        ):
            log(provider_info)
            raise QuietExit("warning: Given information is same as the cluster's saved info. Nothing to do.")

        tx = self._update_provider_info(f"0x{gpg_fingerprint}", gmail, f_id, ipfs_id)
        return self.tx_id(tx)
    except Exception as e:
        raise e


def update_provider_info(self, gpg_fingerprint, gmail, f_id, ipfs_id):
    """Update provider information."""
    if len(f_id) >= 128:
        raise Exception("federation_cloud_id should be less than 128")

    if len(gmail) >= 128:
        raise Exception("e-mail should be less than 128")

    if gpg_fingerprint[:2] == "0x":
        log(f"gpg_fingerprint={gpg_fingerprint} should not start with 0x")
        raise QuietExit

    if len(gpg_fingerprint) != 40:
        log(f"gpg_fingerprint={gpg_fingerprint} length should be 40")
        raise QuietExit

    return self.is_provider_info_match(gmail, ipfs_id, gpg_fingerprint, f_id)


if __name__ == "__main__":
    Ebb = cfg.Ebb
    ipfs_id = get_ipfs_id()
    ip_address = get_ip()
    if ip_address not in ipfs_id:
        # public IP should exists in the ipfs id
        ipfs_id = re.sub("ip4.*?tcp", f"ip4/{ip_address}/tcp", ipfs_id, flags=re.DOTALL)

    gpg_fingerprint = cfg.ipfs.get_gpg_fingerprint(env.GMAIL)
    f_id = env.OC_USER
    log(f"## gmail=[magenta]{env.GMAIL}")
    log(f"## gpg_fingerprint={gpg_fingerprint}")
    log(f"## ipfs_id=[magenta]{ipfs_id}")
    log(f"## fid=[magenta]{f_id}")
    try:
        cfg.ipfs.is_gpg_published(gpg_fingerprint)
        tx_hash = Ebb.update_provider_info(gpg_fingerprint, env.GMAIL, f_id, ipfs_id)
        receipt = get_tx_status(tx_hash)
    except Exception as e:
        print_tb(e)
