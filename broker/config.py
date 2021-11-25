#!/usr/bin/env python3

import logging
import threading
from contextlib import suppress
from logging import Filter
from pathlib import Path

from broker import cfg
from broker._utils import _log, colored_traceback
from broker._utils.tools import mkdir
from broker._utils.yaml import Yaml
from broker.env import ENV_BASE

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
        with suppress(Exception):
            from brownie import accounts

            accounts.load("alpy.json", "alper")

        # load_dotenv(dotenv_path=self.env_file)

        self.SLURMUSER = self.cfg["provider"]["slurmuser"]
        self.GDRIVE = self.cfg["gdrive"]
        self.OC_USER = self.cfg["oc_user"]
        if "@b2drop.eudat.eu" not in self.OC_USER:
            self.F_ID = f"{self.OC_USER}@b2drop.eudat.eu"
        else:
            self.F_ID = self.OC_USER

        self.DATADIR = Path(self.cfg["datadir"])
        self.LOG_PATH = Path(self.cfg["log_path"])
        self.config = Yaml(self.LOG_PATH.joinpath("config.yaml"))
        self.IS_GETH_TUNNEL = self.cfg["provider"]["is_geth_tunnel"]
        self.IS_IPFS_USE = self.cfg["provider"]["is_ipfs_use"]
        self.IS_EUDAT_USE = self.cfg["provider"]["is_eudat_use"]
        self.IS_GDRIVE_USE = self.cfg["provider"]["is_gdrive_use"]
        self.RPC_PORT = self.cfg["rpc_port"]
        self.BASH_SCRIPTS_PATH = Path(self.cfg["ebloc_path"]) / "broker" / "bash_scripts"
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
        self.PROVIDER_ID = cfg.w3.toChecksumAddress(self.cfg["eth_address"])
        _log.DRIVER_LOG = self.LOG_PATH.joinpath("provider.log")
        mkdir(self.LOG_PATH / "transactions" / self.PROVIDER_ID)
        # self.BLOCK_READ_FROM_FILE = f"{self.LOG_PATH}/block_continue.txt"
        mkdir("/tmp/run")
        self.DRIVER_LOCKFILE = "/tmp/run/driver_popen.pid"
        self.DRIVER_DAEMON_LOCK = "/tmp/run/driverdaemon.pid"
        if isinstance(self.cfg["provider"]["is_thread"], bool):
            cfg.IS_THREADING_ENABLED = self.cfg["provider"]["is_thread"]
        else:
            raise Exception("is_thead should be bool variable")

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


RECONNECT_ATTEMPTS = 5
RECONNECT_SLEEP = 15
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
env: ENV = ENV()
with suppress(Exception):
    env: ENV = ENV()
