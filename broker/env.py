#!/usr/bin/env python3

import os
from pathlib import Path
from sys import platform

from broker._utils.yaml import Yaml
from broker.errors import QuietExit


class ENV_BASE:
    def __init__(self) -> None:
        self.HOME: Path = Path.home()
        hidden_base = self.HOME / ".ebloc-broker"
        fn = hidden_base / "cfg.yaml"
        if not os.path.isfile(fn):
            if not os.path.isdir(hidden_base):
                raise QuietExit(f"E: {hidden_base} is not initialized")

            raise QuietExit(f"E: {fn} is not created")

        self.cfg_yaml = Yaml(fn)
        self.cfg = self.cfg_yaml["cfg"]
        self.WHOAMI = self.cfg["whoami"]
        if platform in ("linux", "linux2"):
            self._HOME = Path("/home") / self.WHOAMI
        elif platform == "darwin":
            self._HOME = Path("/Users") / self.WHOAMI
        elif platform == "win32":
            print("E: does not work in windows")
            exit(1)

        self.EBLOCPATH = Path(self.cfg["ebloc_path"])
        self.CONTRACT_PROJECT_PATH = self._HOME / "ebloc-broker" / "contract"
        self.IS_BLOXBERG = True
        if self.IS_BLOXBERG:
            self.IS_EBLOCPOA = False  # eblocpoa is not in use
            self.IS_GETH_TUNNEL = False

        self.CONTRACT_YAML_FILE = self.EBLOCPATH / "broker" / "eblocbroker_scripts" / "contract.yaml"
        try:
            _yaml = Yaml(self.CONTRACT_YAML_FILE)
            if self.IS_BLOXBERG:
                _yaml = _yaml["networks"]["bloxberg"]
            elif self.IS_EBLOCPOA:
                _yaml = _yaml["networks"]["eblocpoa"]

            self.CONTRACT_ADDRESS = _yaml["address"]
        except Exception as e:
            raise e
