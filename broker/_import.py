#!/usr/bin/env python3

import time
from contextlib import suppress

from broker import cfg
from broker._utils._log import ok
from broker.config import env
from broker.imports import nc
from broker.utils import log
from brownie import network


def reconnect():
    """Attemp to reconnect."""

    log(f"E: {network.show_active()} is not connected through {env.BLOXBERG_HOST}")
    if cfg.NETWORK_ID == "bloxberg":
        cfg.NETWORK_ID = "bloxberg_core"
    elif cfg.NETWORK_ID == "bloxberg_core":
        with suppress(Exception):
            nc(cfg.BERG_CMPE_IP, 8545)
            cfg.NETWORK_ID = "bloxberg"

    log(f"Trying at {cfg.NETWORK_ID}... ", end="")
    network.connect(cfg.NETWORK_ID)
    log(ok())


def check_connection(is_silent=False):
    if not network.is_connected():
        try:
            reconnect()
        except Exception as e:
            log(f"E: {e}")

        if not network.is_connected():
            time.sleep(15)
    elif not is_silent:
        log(f"Attempt to connect bloxberg through [g]{cfg.NETWORK_ID}[/g] {ok()}", is_write=False)
