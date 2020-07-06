#!/usr/bin/env python3

import logging
import os
import threading
from logging import Filter
from os.path import expanduser
from pathlib import Path

from dotenv import load_dotenv

import _utils.colored_traceback as colored_traceback
import _utils.colorer  # NOQA

# from typing import Type
# from web3 import Web3


class ThreadFilter(Filter):
    """Only accept log records from a specific thread or thread name"""

    def __init__(self, thread_id=None, thread_name=None):
        if thread_id is None and thread_name is None:
            raise ValueError("Must set at a thread_id and/or thread_name to filter on")

        self._threadid = thread_id
        self._thread_name = thread_name

    def filter(self, record):
        if self._threadid is not None and record.thread != self._threadid:
            return False
        if self._thread_name is not None and record.threadName != self._thread_name:
            return False
        return True


class IgnoreThreadsFilter(Filter):
    """Only accepts log records that originated from the main thread"""

    def __init__(self):
        self._main_thread_id = threading.main_thread().ident

    def filter(self, record):
        return record.thread == self._main_thread_id


class Web3NotConnected(Exception):
    pass


class QuietExit(Exception):
    pass


class ENV:
    def __init__(self) -> None:
        self.HOME = expanduser("~")
        env_path = Path(f"{self.HOME}/.eBlocBroker/") / ".env"
        load_dotenv(dotenv_path=env_path)
        self.log_filename = None
        self.WHOAMI = os.getenv("WHOAMI")
        self.SLURMUSER = os.getenv("SLURMUSER")
        self.LOG_PATH = os.getenv("LOG_PATH")
        self.GDRIVE = os.getenv("GDRIVE")
        self.OC_USER = os.getenv("OC_USER")
        self.IPFS_USE = str(os.getenv("IPFS_USE")).lower() in ("yes", "true", "t", "1")
        self.EUDAT_USE = str(os.getenv("EUDAT_USE")).lower() in ("yes", "true", "t", "1",)
        self.GDRIVE_USE = str(os.getenv("EUDAT_USE")).lower() in ("yes", "true", "t", "1",)

        self.EBLOCPATH = os.getenv("EBLOCPATH")
        self.POA_CHAIN = str(os.getenv("POA_CHAIN")).lower() in ("yes", "true", "t", "1",)
        self.RPC_PORT = os.getenv("RPC_PORT")

        # self.GDRIVE_CLOUD_PATH = f"/home/{self.WHOAMI}/foo"
        self.GDRIVE_METADATA = f"/home/{self.WHOAMI}/.gdrive"
        self.IPFS_REPO = f"/home/{self.WHOAMI}/.ipfs"
        self.IPFS_LOG = f"{self.LOG_PATH}/ipfs.out"
        self.GANACHE_LOG = f"{self.LOG_PATH}/ganache.out"
        self.OWNCLOUD_PATH = "/oc"

        self.PROGRAM_PATH = "/var/eBlocBroker"
        self.JOBS_READ_FROM_FILE = f"{self.LOG_PATH}/test.txt"
        self.CANCEL_JOBS_READ_FROM_FILE = f"{self.LOG_PATH}/cancelledJobs.txt"
        self.BLOCK_READ_FROM_FILE = f"{self.LOG_PATH}/block_continue.txt"

        self.CANCEL_BLOCK_READ_FROM_FILE = f"{self.LOG_PATH}/cancelledBlockReadFrom.txt"
        self.OC_CLIENT = f"{self.LOG_PATH}/.oc_client.pckl"
        self.OC_CLIENT_REQUESTER = f"{self.LOG_PATH}/.oc_client_requester.pckl"

        self.WHISPER_INFO = f"{self.LOG_PATH}/whisper_info.txt"
        self.WHISPER_LOG = f"{self.LOG_PATH}/whisper_state_receiver.out"
        self.WHISPER_TOPIC = "0x07678231"
        self.IS_THREADING_ENABLED = False

        if w3:
            self.PROVIDER_ID = w3.toChecksumAddress(os.getenv("PROVIDER_ID"))
        else:
            self.PROVIDER_ID = None

    def set_provider_id(self, provider_id=None):
        if not os.getenv("PROVIDER_ID"):
            if provider_id:
                print(w3)
                self.PROVIDER_ID = w3.toChecksumAddress(provider_id)
            else:
                print("E: Please set PROVIDER_ID in ~/.eBlocBroker/.env")
        else:
            self.PROVIDER_ID = w3.toChecksumAddress(os.getenv("PROVIDER_ID"))


def setup_logger(log_path="", is_brownie=False):
    _log = logging.getLogger()  # root logger
    for hdlr in _log.handlers[:]:  # remove all old handlers
        _log.removeHandler(hdlr)

    if is_brownie:
        logging.basicConfig(
            level=logging.INFO, format="[%(funcName)21s():%(lineno)3s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S",
        )
    elif log_path:
        env.log_filename = log_path
        # Attach the IgnoreThreadsFilter to the main root log handler
        # This is responsible for ignoring all log records originating from
        # new threads.
        main_handler = logging.FileHandler(log_path, "a")
        main_handler.addFilter(IgnoreThreadsFilter())

        logging.basicConfig(
            handlers=[logging.StreamHandler(), main_handler],
            level=logging.INFO,
            # handlers=[logging.StreamHandler(), logging.FileHandler(log_path)],
            # format="%(asctime)s %(levelname)-8s [%(module)s %(lineno)d] %(message)s",
            # format="%(asctime)s %(levelname)-8s [%(filename)15s:%(lineno)s - %(funcName)21s()] %(message)s",
            format="[%(asctime)s %(filename)15s:%(lineno)s - %(funcName)21s()] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        # logger.info("Log_path => %s", log_path)
    else:  # only stdout
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s %(filename)15s:%(lineno)s - %(funcName)21s()] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    return logging.getLogger()


Ebb = None
w3 = None  # # type: Type[Web3]
contract = None

coll = None
oc = None
driver_cancel_process = None
whisper_state_receiver_process = None
colored_traceback.add_hook(always=True)
env = ENV()
logger = setup_logger()  # Default initialization

RECONNECT_ATTEMPTS = 5
RECONNECT_SLEEP = 15
IS_THREADING_ENABLED = False
