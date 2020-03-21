#!/usr/bin/env python3

import logging
import os
from os.path import expanduser
from pdb import set_trace as bp  # noqa: F401

from dotenv import load_dotenv

import Colorer  # noqa: F401

eBlocBroker = None
w3 = None
driver_cancel_process = None
whisper_state_receiver_process = None

HOME = expanduser("~")
# Load .env from the given path
load_dotenv(os.path.join(f"{HOME}/.eBlocBroker/", ".env"))

EBLOCPATH = os.getenv("EBLOCPATH")
POA_CHAIN = str(os.getenv("POA_CHAIN")).lower() in ("yes", "true", "t", "1")
RPC_PORT = os.getenv("RPC_PORT")


def load_log(log_path=""):
    log = logging.getLogger()  # root logger
    for hdlr in log.handlers[:]:  # remove all old handlers
        log.removeHandler(hdlr)

    if log_path:
        logging.basicConfig(
            level=logging.INFO,
            # format="%(asctime)s %(levelname)-8s [%(module)s %(lineno)d] %(message)s",
            # format="%(asctime)s %(levelname)-8s [%(filename)15s:%(lineno)s - %(funcName)21s()] %(message)s",
            format="[%(asctime)s %(filename)15s:%(lineno)s - %(funcName)21s()] %(message)s",
            handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
            datefmt='%Y-%m-%d %H:%M:%S',
        )
    else:
        logging.basicConfig(
            level=logging.INFO, format="[%(asctime)s %(filename)15s:%(lineno)s - %(funcName)21s()] %(message)s",
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    return logging
