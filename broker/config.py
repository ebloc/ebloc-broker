#!/usr/bin/env python3

import logging
import os
import threading
from contextlib import suppress
from logging import Filter
from os.path import expanduser
from pathlib import Path
from typing import Union

from dotenv import load_dotenv

import broker._utils.colored_traceback as colored_traceback
import broker._utils.tools as tools
import broker.cfg as cfg
from broker._utils.yaml import Yaml

logging.getLogger("filelock").setLevel(logging.ERROR)

class Terminate(Exception):  # noqa
    pass


class ThreadFilter(Filter):
    """Only accept log records from a specific thread or thread name."""

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
    """Only accepts log records that originated from the main thread."""

    def __init__(self):
        self._main_thread_id = threading.main_thread().ident

    def filter(self, record):
        return record.thread == self._main_thread_id


class ENV:
    """ENV class that contains configuration values."""

    def __init__(self) -> None:
        try:
            from brownie import accounts

            accounts.load("alpy.json", "alper")
        except:
            pass

        self.HOME = expanduser("~")
        env_file = Path(f"{self.HOME}/.ebloc-broker/") / ".env"
        _env = dict()
        try:
            with open(env_file) as f:
                for line in f:
                    if line.startswith("#") or not line.strip():
                        continue
                    key, value = line.strip().split("=", 1)
                    _env[key] = value.replace('"', "").split("#", 1)[0].rstrip()
        except IOError:
            raise Exception(f"E: File '{env_file}' is not accessible")

        true_set = ("yes", "true", "t", "1")
        load_dotenv(dotenv_path=env_file)
        self.WHOAMI = _env["WHOAMI"]
        self.SLURMUSER = _env["SLURMUSER"]
        self.LOG_PATH = _env["LOG_PATH"]
        self.GDRIVE = _env["GDRIVE"]
        self.OC_USER = _env["OC_USER"]
        self.DATADIR = _env["DATADIR"]
        self.config = Yaml(f"{self.LOG_PATH}/config.yaml")
        self.IS_GETH_TUNNEL = str(_env["IS_GETH_TUNNEL"]).lower() in true_set
        self.IS_IPFS_USE = str(_env["IS_IPFS_USE"]).lower() in true_set
        self.IS_EUDAT_USE = str(_env["IS_EUDAT_USE"]).lower() in true_set
        self.IS_GDRIVE_USE = str(_env["IS_GDRIVE_USE"]).lower() in true_set
        self.IS_BLOXBERG = str(_env["IS_BLOXBERG"]).lower() in true_set
        self.IS_EBLOCPOA = str(_env["IS_EBLOCPOA"]).lower() in true_set
        self.IS_DRIVER = False
        self.RPC_PORT = _env["RPC_PORT"]
        self.EBLOCPATH = _env["EBLOCPATH"]
        self.BASE_DATA_PATH = _env["BASE_DATA_PATH"]

        # self.GDRIVE_CLOUD_PATH = f"/home/{self.WHOAMI}/foo"
        self.GDRIVE_METADATA = f"/home/{self.WHOAMI}/.gdrive"
        self.IPFS_REPO = f"/home/{self.WHOAMI}/.ipfs"
        self.IPFS_LOG = f"{self.LOG_PATH}/ipfs.out"
        self.GANACHE_LOG = f"{self.LOG_PATH}/ganache.out"
        self.OWNCLOUD_PATH = "/oc"
        self.PROGRAM_PATH = "/var/ebloc-broker"
        self.LINKS = f"{self.LOG_PATH}/links"
        self.JOBS_READ_FROM_FILE = f"{self.LOG_PATH}/test.txt"
        self.CANCEL_JOBS_READ_FROM_FILE = f"{self.LOG_PATH}/cancelledJobs.txt"
        self.GPG_PASS_FILE = f"{self.LOG_PATH}/.gpg_pass.txt"
        self.CANCEL_BLOCK_READ_FROM_FILE = f"{self.LOG_PATH}/cancelledBlockReadFrom.txt"
        self.OC_CLIENT = f"{self.LOG_PATH}/.oc_client.pckl"
        self.OC_CLIENT_REQUESTER = f"{self.LOG_PATH}/.oc_client_requester.pckl"
        self.IS_THREADING_ENABLED = False
        self.PROVIDER_ID = None  # type: Union[str, None]
        tools.DRIVER_LOG = f"{self.LOG_PATH}/provider.log"
        # self.BLOCK_READ_FROM_FILE = f"{self.LOG_PATH}/block_continue.txt"

        if cfg.w3:
            self.PROVIDER_ID = cfg.w3.toChecksumAddress(_env["PROVIDER_ID"])

        if not os.path.isdir("/tmp/run"):
            os.makedirs("/tmp/run")  # mkdir

        self.DRIVER_LOCKFILE = "/tmp/run/driver_popen.pid"
        self.DRIVER_DAEMON_LOCK = "/tmp/run/driverdaemon.pid"

    def set_provider_id(self, provider_id=None):
        if not os.getenv("PROVIDER_ID"):
            if provider_id:
                self.PROVIDER_ID = cfg.w3.toChecksumAddress(provider_id)
            else:
                print("E: Please set PROVIDER_ID in ~/.ebloc-broker/.env")
                raise tools.QuietExit
        else:
            self.PROVIDER_ID = cfg.w3.toChecksumAddress(os.getenv("PROVIDER_ID"))


def setup_logger(log_path="", is_brownie=False):
    _log = logging.getLogger()  # root logger
    for hdlr in _log.handlers[:]:  # remove all old handlers
        _log.removeHandler(hdlr)

    if is_brownie:
        logging.basicConfig(
            level=logging.INFO,
            format="[%(funcName)21s():%(lineno)3s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    elif log_path:
        tools.ll.LOG_FILENAME = log_path
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
            datefmt="%H:%M:%S",
            # datefmt="%Y-%m-%d %H:%M:%S",
        )
        # logger.info("Log_path => %s", log_path)
    else:  # only stdout
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s %(filename)15s:%(lineno)s - %(funcName)21s()] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    return logging.getLogger()


Ebb = None  # eBlocBlock Contract Class
ebb = None  # eBlocBroker Contract on the blockchain
contract = None
chain = None
w3_ebb = None
ipfs = None

colored_traceback.add_hook(always=True)
logger = setup_logger()  # Default initialization

coll = None
oc = None
driver_cancel_process = None
_eBlocBroker = None
BLOCK_DURATION = 15
RECONNECT_ATTEMPTS = 5
RECONNECT_SLEEP = 15
IS_THREADING_ENABLED = False

with suppress(Exception):
    env: ENV = ENV()
