#!/usr/bin/env python3

import json
from pathlib import Path

import ruamel.yaml

from broker._utils._log import log


def add_bloxberg_config(fname):
    bloxberg_config = {
        "name": "bloxberg (Bloxberg)",
        "id": "bloxberg",
        "chainid": 8995,
        "host": "https://core.bloxberg.org",
        "explorer": "https://blockexplorer.bloxberg.org/api",
    }
    config, ind, bsi = ruamel.yaml.util.load_yaml_guess_indent(open(fname))
    data = config

    is_bloxberg_added = False
    for config in data["live"]:
        if config["name"] == "Ethereum":
            for network in config["networks"]:
                if "bloxberg" in network["name"]:
                    is_bloxberg_added = True
                    if json.loads(json.dumps(network)) == bloxberg_config:
                        log(f"## bloxberg config is already added into {fname}")
                    else:
                        network["name"] = bloxberg_config["name"]
                        network["id"] = bloxberg_config["id"]
                        network["chainid"] = bloxberg_config["chainid"]
                        network["host"] = bloxberg_config["host"]
                        network["explorer"] = bloxberg_config["explorer"]

            if not is_bloxberg_added:
                config["networks"].append(bloxberg_config)

    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=ind, sequence=ind, offset=bsi)
    with open(fname, "w") as fp:
        yaml.dump(data, fp)


fname = Path.home() / ".brownie" / "network-config.yaml"
add_bloxberg_config(fname)
