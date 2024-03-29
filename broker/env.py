#!/usr/bin/env python3

import os
import sys
from pathlib import Path
from sys import platform

from broker._utils.yaml import Yaml
from broker.errors import QuietExit


def is_docker():
    path = "/proc/self/cgroup"
    return os.path.exists("/.dockerenv") or os.path.isfile(path) and any("docker" in line for line in open(path))


class ENV_BASE:
    def __init__(self) -> None:
        self.HOME: Path = Path.home()
        hidden_base_dir = self.HOME / ".ebloc-broker"
        fn = hidden_base_dir / "cfg.yaml"
        if not os.path.isfile(fn):
            if not os.path.isdir(hidden_base_dir):
                raise QuietExit(f"E: {hidden_base_dir} is not initialized.\nRun: eblocbroker init")

            raise QuietExit(f"E: {fn} is not created")

        try:
            self.cfg_yaml = Yaml(fn)
        except Exception as e:
            raise QuietExit(f"E: {e}: ~/.ebloc-broker/cfg.yaml is broken") from e

        self.cfg = self.cfg_yaml["cfg"]
        self.WHOAMI = self.cfg["whoami"]
        if platform in ("linux", "linux2"):
            self._HOME = Path("/") / "home" / self.WHOAMI
        elif platform == "darwin":
            self._HOME = Path("/") / "Users" / self.WHOAMI
        elif platform == "win32":
            print("E: does not work in Windows")
            sys.exit(1)

        if is_docker():
            self._HOME = Path("/") / "root"

        self.IPFS_REPO = self.tilda_check(self.cfg["ipfs_repo_dir"])
        self.EBLOCPATH = self.tilda_check(Path(self.cfg["ebloc_path"]))
        self.CONTRACT_PROJECT_PATH = self.EBLOCPATH / "contract"
        self.IS_TESTNET = True
        if self.IS_TESTNET:
            self.IS_EBLOCPOA = False  # eblocpoa is not in use
            self.IS_GETH_TUNNEL = False

        self.EBB_SCRIPTS = self.EBLOCPATH / "broker" / "eblocbroker_scripts"
        self.CONTRACT_YAML_FILE = self.EBB_SCRIPTS / "contract.yaml"
        try:
            _yaml = Yaml(self.CONTRACT_YAML_FILE)
            if self.IS_TESTNET:
                self.ACTIVE_NETWORK = _yaml["networks"]["active_network"]
                _yaml = _yaml["networks"][self.ACTIVE_NETWORK]
            elif self.IS_EBLOCPOA:
                _yaml = _yaml["networks"]["eblocpoa"]

            self.CONTRACT_ADDRESS = _yaml["eBlocBroker"]["address"]
            self.TOKEN_CONTRACT_ADDRESS = _yaml["USDTmy"]["address"]
            #
            self.ROC_CONTRACT_ADDRESS = _yaml["ResearchCertificate"]["address"]
            self.AUTO_CONTRACT_ADDRESS = _yaml["AutonomousSoftwareOrg"]["address"]
        except Exception as e:
            raise e

    def tilda_check(self, _str) -> Path:
        _str = str(_str)
        if "~/" in _str[0:2]:
            return Path(_str.replace("~", str(self._HOME)))

        return Path(_str)
