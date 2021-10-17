#!/usr/bin/env python3

import logging
import os
import threading
from contextlib import suppress
from logging import Filter
from pathlib import Path
from typing import Union

from dotenv import load_dotenv

import broker._utils._log as _log
import broker._utils.colored_traceback as colored_traceback
import broker.cfg as cfg
from broker._utils.tools import QuietExit
from broker._utils.yaml import Yaml

logging.getLogger("filelock").setLevel(logging.ERROR)


class Terminate(Exception):
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

        self.HOME: Path = Path.home()
        env_file = self.HOME / ".ebloc-broker" / ".env"
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
        self.BLOCK_DURATION = 15
        self.WHOAMI = _env["WHOAMI"]
        self.SLURMUSER = _env["SLURMUSER"]
        self.GDRIVE = _env["GDRIVE"]
        self.OC_USER = _env["OC_USER"]
        self.DATADIR = Path(_env["DATADIR"])
        self.LOG_PATH = Path(_env["LOG_PATH"])
        self.config = Yaml(self.LOG_PATH.joinpath("config.yaml"))
        self.IS_GETH_TUNNEL = str(_env["IS_GETH_TUNNEL"]).lower() in true_set
        self.IS_IPFS_USE = str(_env["IS_IPFS_USE"]).lower() in true_set
        self.IS_EUDAT_USE = str(_env["IS_EUDAT_USE"]).lower() in true_set
        self.IS_GDRIVE_USE = str(_env["IS_GDRIVE_USE"]).lower() in true_set
        self.IS_BLOXBERG = str(_env["IS_BLOXBERG"]).lower() in true_set
        self.IS_EBLOCPOA = str(_env["IS_EBLOCPOA"]).lower() in true_set
        self.IS_DRIVER = False
        self.RPC_PORT = _env["RPC_PORT"]
        self.EBLOCPATH = Path(_env["EBLOCPATH"])
        self.BASE_DATA_PATH = Path(_env["BASE_DATA_PATH"])

        # self.GDRIVE_CLOUD_PATH = f"/home/{self.WHOAMI}/foo"
        self._HOME = Path("/home") / self.WHOAMI
        self.GDRIVE_METADATA = self._HOME.joinpath(".gdrive")
        self.IPFS_REPO = self._HOME.joinpath(".ipfs")
        self.IPFS_LOG = self.LOG_PATH.joinpath("ipfs.out")
        self.GANACHE_LOG = self.LOG_PATH.joinpath("ganache.out")
        self.OWNCLOUD_PATH = Path("/oc")
        self.PROGRAM_PATH = Path("/var") / "ebloc-broker"
        self.LINK_PATH = self.LOG_PATH.joinpath("links")
        self.JOBS_READ_FROM_FILE = self.LOG_PATH.joinpath("test.txt")
        self.CANCEL_JOBS_READ_FROM_FILE = self.LOG_PATH.joinpath("cancelledJobs.txt")
        self.GPG_PASS_FILE = self.LOG_PATH.joinpath(".gpg_pass.txt")
        self.CANCEL_BLOCK_READ_FROM_FILE = self.LOG_PATH.joinpath("cancelled_block_read_from.txt")
        self.OC_CLIENT = self.LOG_PATH.joinpath(".oc_client.pckl")
        self.OC_CLIENT_REQUESTER = self.LOG_PATH.joinpath(".oc_client_requester.pckl")
        _log.DRIVER_LOG = self.LOG_PATH.joinpath("provider.log")
        self.IS_THREADING_ENABLED = False
        self.PROVIDER_ID = None  # type: Union[str, None]
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
                print(f"E: Please set PROVIDER_ID in {self.env_file}")
                raise QuietExit
        else:
            self.PROVIDER_ID = cfg.w3.toChecksumAddress(os.getenv("PROVIDER_ID"))


def setup_logger(log_path="", is_brownie=False):
    """Set logger path also for the log() function."""
    logger = logging.getLogger()  # root logger
    for hdlr in logger.handlers[:]:  # remove all old handlers
        logger.removeHandler(hdlr)

    if is_brownie:
        logging.basicConfig(
            level=logging.INFO,
            format="[%(funcName)21s():%(lineno)3s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    elif log_path:
        _log.ll.LOG_FILENAME = log_path
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
ipfs = None
w3_ebb = None

colored_traceback.add_hook(always=True)
logger = setup_logger()  # Default initialization

coll = None
oc = None
driver_cancel_process = None
_eBlocBroker = None
RECONNECT_ATTEMPTS = 5
RECONNECT_SLEEP = 15
IS_THREADING_ENABLED = False

with suppress(Exception):
    env: ENV = ENV()
