#!/usr/bin/env python3

import logging
import os
from os.path import expanduser
from pdb import set_trace as bp  # noqa: F401

from dotenv import load_dotenv

import _utils.colorer  # noqa: F401

eBlocBroker = None
w3 = None
driver_cancel_process = None
whisper_state_receiver_process = None
env = None


class ENV:
    def __init__(self) -> None:
        self.HOME = expanduser("~")
        # Load .env from the given path
        load_dotenv(os.path.join(f"{self.HOME}/.eBlocBroker/", ".env"))

        self.WHOAMI = os.getenv("WHOAMI")
        self.SLURMUSER = os.getenv("SLURMUSER")
        self.LOG_PATH = os.getenv("LOG_PATH")
        self.GDRIVE = os.getenv("GDRIVE")
        self.OC_USER = os.getenv("OC_USER")
        self.IPFS_USE = str(os.getenv("IPFS_USE")).lower() in ("yes", "true", "t", "1")
        self.EUDAT_USE = str(os.getenv("EUDAT_USE")).lower() in ("yes", "true", "t", "1")
        self.GDRIVE_USE = str(os.getenv("EUDAT_USE")).lower() in ("yes", "true", "t", "1")

        self.EBLOCPATH = os.getenv("EBLOCPATH")
        self.POA_CHAIN = str(os.getenv("POA_CHAIN")).lower() in ("yes", "true", "t", "1")
        self.RPC_PORT = os.getenv("RPC_PORT")

        self.GDRIVE_CLOUD_PATH = f"/home/{self.WHOAMI}/foo"
        self.GDRIVE_METADATA = f"/home/{self.WHOAMI}/.gdrive"
        self.IPFS_REPO = f"/home/{self.WHOAMI}/.ipfs"
        self.OWN_CLOUD_PATH = "/oc"

        self.PROGRAM_PATH = "/var/eBlocBroker"
        self.JOBS_READ_FROM_FILE = f"{self.LOG_PATH}/test.txt"
        self.CANCEL_JOBS_READ_FROM_FILE = f"{self.LOG_PATH}/cancelledJobs.txt"
        self.BLOCK_READ_FROM_FILE = f"{self.LOG_PATH}/blockReadFrom.txt"
        self.CANCEL_BLOCK_READ_FROM_FILE = f"{self.LOG_PATH}/cancelledBlockReadFrom.txt"
        if w3:
            self.PROVIDER_ID = w3.toChecksumAddress(os.getenv("PROVIDER_ID"))
        else:
            self.PROVIDER_ID = None

    def set_provider_id(self):
        self.PROVIDER_ID = w3.toChecksumAddress(os.getenv("PROVIDER_ID"))


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
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s %(filename)15s:%(lineno)s - %(funcName)21s()] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    return logging
