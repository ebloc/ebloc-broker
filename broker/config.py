#!/usr/bin/env python3

import logging
import socket
import threading
from logging import Filter
from pathlib import Path
from web3.contract import Contract

from broker import cfg
from broker._utils import _log, colored_traceback
from broker._utils.tools import mkdir
from broker._utils.yaml import Yaml
from broker.env import ENV_BASE
from broker.errors import QuietExit
from broker.python_scripts.add_bloxberg_into_network_config import read_network_config

logging.getLogger("filelock").setLevel(logging.ERROR)


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


class ENV(ENV_BASE):
    """ENV class that contains configuration values."""

    def __init__(self) -> None:
        super().__init__()
        if "provider" in self.cfg:
            self.IS_PROVIDER = True
            self.SLURMUSER = self.cfg["provider"]["slurm_user"]
            self.IS_IPFS_USE = self.cfg["provider"]["is_ipfs_use"]
            self.IS_B2DROP_USE = self.cfg["provider"]["is_b2drop_use"]
            self.IS_GDRIVE_USE = self.cfg["provider"]["is_gdrive_use"]
            if isinstance(self.cfg["provider"]["is_thread"], bool):
                cfg.IS_THREADING_ENABLED = self.cfg["provider"]["is_thread"]
        else:
            self.IS_PROVIDER = False

        # with suppress(Exception):
        #     from brownie import accounts

        #     accounts.load("alpy.json", "alper")

        self.PROGRAM_PATH = Path("/") / "var" / "ebloc-broker"
        self.GDRIVE = self.cfg["gdrive"]
        if "datadir" in self.cfg:
            self.DATADIR = Path(self.cfg["datadir"])
        else:
            self.DATADIR = None

        self.LOG_DIR = Path(self.cfg["log_path"])
        try:
            self.BLOXBERG_HOST = read_network_config(cfg.NETWORK_ID)
        except:
            self.BLOXBERG_HOST = "https://core.bloxberg.org"

        # if "bloxberg_host" in self.cfg:
        #     self.BLOXBERG_HOST = self.cfg["bloxberg_host"]
        self.config = Yaml(self.LOG_DIR.joinpath("config.yaml"))
        self.BASH_SCRIPTS_PATH = Path(self.cfg["ebloc_path"]) / "broker" / "bash_scripts"
        self.GDRIVE_METADATA = self._HOME.joinpath(".gdrive")
        self.IPFS_REPO = self._HOME.joinpath(".ipfs")
        if socket.gethostname() == "homevm":
            self.IPFS_REPO = "/mnt/hgfs/ggh/.ipfs"

        self.IPFS_LOG = self.LOG_DIR.joinpath("ipfs.out")
        self.GANACHE_LOG = self.LOG_DIR.joinpath("ganache.out")
        self.OWNCLOUD_PATH = Path("/mnt/oc")
        self.LINK_PATH = self.LOG_DIR.joinpath("links")
        self.JOBS_READ_FROM_FILE = self.LOG_DIR.joinpath("test.txt")
        self.GPG_PASS_FILE = self.LOG_DIR.joinpath(".gpg_pass.txt")
        self.CANCEL_JOBS_READ_FROM_FILE = self.LOG_DIR.joinpath("cancelled_jobs.txt")
        self.CANCEL_BLOCK_READ_FROM_FILE = self.LOG_DIR.joinpath("cancelled_block_read_from.txt")
        self.OC_CLIENT = self.LOG_DIR.joinpath(".oc_client.pckl")
        self.PROVIDER_ID = cfg.w3.toChecksumAddress(self.cfg["eth_address"].lower())
        self.OC_USER = self.cfg["oc_username"].replace("@b2drop.eudat.eu", "")
        if "rpc_port" in self.cfg:
            self.RPC_PORT = self.cfg["rpc_port"]
        else:
            self.RPC_PORT = 8545

        _log.DRIVER_LOG = self.LOG_DIR.joinpath("provider.log")
        mkdir(self.LOG_DIR / "transactions" / self.PROVIDER_ID.lower())
        # self.BLOCK_READ_FROM_FILE = f"{self.LOG_DIR}/block_continue.txt"
        mkdir("/tmp/run")
        self.DRIVER_LOCKFILE = "/tmp/run/driver_popen.pid"
        self.DRIVER_DAEMON_LOCK = "/tmp/run/driverdaemon.pid"
        self.GMAIL = self.cfg["gmail"]


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


Ebb = cfg.Ebb
ipfs = cfg.ipfs
ebb: Contract = None  # ebloc-broker contract object on the blockchain

contract = None
chain = None
w3_ebb = None
colored_traceback.add_hook(always=True)
logger = setup_logger()  # Default initialization
coll = None
oc = None
driver_cancel_process = None
_eblocbroker = None
usdtmy = None
_usdtmy = None
env: ENV
try:
    env = ENV()
except Exception as e:
    print(e)
    raise QuietExit from e
