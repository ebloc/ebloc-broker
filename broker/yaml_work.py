#!/usr/bin/env python3

from broker._utils.yaml import Yaml
from pathlib import Path
from broker._utils._log import log
from collections import OrderedDict
import yaml


class YamlUpdate:
    def __init__(self):
        self.config_file = Path.home() / ".brownie" / "alper.yaml"
        self.network_config = Yaml(self.config_file)
        self.change_item()

    def change_item(self):
        for network in self.network_config["live"]:
            if network["name"] == "Ethereum":
                network["name"] = "alper"
                print(self.network_config)


yy = YamlUpdate()
print(yy.config_file.read_text())
