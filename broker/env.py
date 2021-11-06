#!/usr/bin/env python3

from pathlib import Path

from dotenv import load_dotenv

from broker._utils.tools import read_json


class ENV_BASE:
    def __init__(self) -> None:
        self._env = {}
        self.true_set = ("yes", "true", "t", "1")
        self.HOME: Path = Path.home()
        self.env_file = self.HOME / ".ebloc-broker" / ".env"
        try:
            with open(self.env_file) as f:
                for line in f:
                    if line.startswith("#") or not line.strip():
                        continue
                    key, value = line.strip().split("=", 1)
                    self._env[key] = value.replace('"', "").split("#", 1)[0].rstrip()
        except IOError as e:
            raise Exception(f"E: File '{self.env_file}' is not accessible") from e

        load_dotenv(dotenv_path=self.env_file)
        self.WHOAMI = self._env["WHOAMI"]
        self._HOME = Path("/home") / self.WHOAMI
        self.EBLOCPATH = Path(self._env["EBLOCPATH"])
        self.CONTRACT_PROJECT_PATH = self._HOME / "ebloc-broker" / "contract"
        self.IS_BLOXBERG = str(self._env["IS_BLOXBERG"]).lower() in self.true_set
        self.IS_EBLOCPOA = str(self._env["IS_EBLOCPOA"]).lower() in self.true_set
        try:
            if self.IS_BLOXBERG:
                json_file = self.EBLOCPATH / "broker" / "eblocbroker" / "contract_bloxberg.json"
            elif self.IS_EBLOCPOA:
                json_file = self.EBLOCPATH / "broker" / "eblocbroker" / "contract_eblocpoa.json"

            contract = read_json(json_file)
            self.CONTRACT_ADDRESS = contract["address"]
        except Exception as e:
            print(f"E: Couldn't read the contract.json {json_file}")
            raise e
