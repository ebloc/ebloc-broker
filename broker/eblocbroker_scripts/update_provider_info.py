#!/usr/bin/env python3

import re

from broker import cfg
from broker._utils.tools import get_ip, is_gpg_published, log, print_tb
from broker._utils.web3_tools import get_tx_status
from broker.config import env
from broker.eblocbroker_scripts.register_provider import get_ipfs_id
from broker.errors import QuietExit
from broker.lib import run


def update_provider_info(self, gpg_fingerprint, email, federation_cloud_id, ipfs_id):
    """Update provider info."""
    if len(federation_cloud_id) >= 128:
        log("E: federation_cloud_id could be lesser than 128")
        raise

    if len(email) >= 128:
        raise Exception("E: e-mail should be less than 128")

    if gpg_fingerprint[:2] == "0x":
        log(f"E: gpg_fingerprint={gpg_fingerprint} should not start with 0x")
        raise QuietExit

    if len(gpg_fingerprint) != 40:
        log(f"E: gpg_fingerprint={gpg_fingerprint} length should be 40")
        raise QuietExit

    try:
        provider_info = self.get_provider_info(env.PROVIDER_ID)
        if (
            # TODO: control does gpg_finderprint starts with 0x
            provider_info["gpg_fingerprint"] == gpg_fingerprint.lower()
            and provider_info["email"] == email
            and provider_info["f_id"] == federation_cloud_id
            and provider_info["ipfs_id"] == ipfs_id
        ):
            log(provider_info)
            raise QuietExit("Warning: Given information is same with the cluster's saved info. Nothing to do.")

        tx = self._update_provider_info(f"0x{gpg_fingerprint}", email, federation_cloud_id, ipfs_id)
        return self.tx_id(tx)
    except Exception as e:
        raise e


if __name__ == "__main__":
    Ebb = cfg.Ebb
    ipfs_id = get_ipfs_id()
    ip_address = get_ip()
    if ip_address not in ipfs_id:
        # public IP should exists in the ipfs id
        ipfs_id = re.sub("ip4.*?tcp", f"ip4/{ip_address}/tcp", ipfs_id, flags=re.DOTALL)

    email = env.GMAIL
    federation_cloud_id = env.F_ID
    log(f"## gmail=[magenta]{email}")
    gpg_fingerprint = run([env.BASH_SCRIPTS_PATH / "get_gpg_fingerprint.sh"])
    log(f"## gpg_fingerprint={gpg_fingerprint}")
    log(f"## ipfs_id=[magenta]{ipfs_id}")
    try:
        is_gpg_published(gpg_fingerprint)
        tx_hash = Ebb.update_provider_info(gpg_fingerprint, email, federation_cloud_id, ipfs_id)
        receipt = get_tx_status(tx_hash)
    except Exception as e:
        print_tb(e)
