#!/usr/bin/env python3

from pathlib import Path
from broker._utils.yaml import Yaml


class ENV_BASE:
    def __init__(self) -> None:
        # self.true_set = ("yes", "true", "t", "1")
        self.HOME: Path = Path.home()
        self.cfg_yaml = Yaml(self.HOME / ".ebloc-broker" / "cfg.yaml")
        self.cfg = self.cfg_yaml["cfg"]
        self.WHOAMI = self.cfg["whoami"]
        self._HOME = Path("/home") / self.WHOAMI
        self.EBLOCPATH = Path(self.cfg["ebloc_path"])
        self.CONTRACT_PROJECT_PATH = self._HOME / "ebloc-broker" / "contract"
        self.IS_BLOXBERG = self.cfg["provider"]["is_bloxberg"]
        self.IS_EBLOCPOA = self.cfg["provider"]["is_eblocpoa"]
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
