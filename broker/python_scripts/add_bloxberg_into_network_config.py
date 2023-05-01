#!/usr/bin/env python3

import json
import ruamel.yaml
from pathlib import Path

from broker._utils._log import log


def read_network_config(network_id, fn=Path.home() / ".brownie" / "network-config.yaml") -> str:
    config_data, _, _ = ruamel.yaml.util.load_yaml_guess_indent(open(fn))
    for _config in config_data["live"]:
        if _config["name"] == "Ethereum":
            for network in _config["networks"]:
                if network_id in network["id"]:
                    return network["host"]

    raise Exception


def bloxberg_dict(_id, url):
    config = {
        "name": "bloxberg (Bloxberg)",
        "id": _id,
        "chainid": 8995,
        "host": url,
        "explorer": "https://blockexplorer.bloxberg.org/api",
    }
    return config


def add_bloxberg_config(fn):
    bloxberg_config = bloxberg_dict("bloxberg", "http://berg-cmpe-boun.duckdns.org:8545")
    bloxberg_config_core = bloxberg_dict("bloxberg_core", "https://core.bloxberg.org")
    config_data, ind, bsi = ruamel.yaml.util.load_yaml_guess_indent(open(fn))
    is_bloxberg_added = False
    for _config in config_data["live"]:
        if _config["name"] == "Ethereum":
            for network in _config["networks"]:
                if "bloxberg" in network["name"]:
                    is_bloxberg_added = True
                    if json.loads(json.dumps(network)) == bloxberg_config:
                        log(f"## bloxberg config is already added into {fn}")
                    else:
                        network["name"] = bloxberg_config["name"]
                        network["id"] = bloxberg_config["id"]
                        network["chainid"] = bloxberg_config["chainid"]
                        network["host"] = bloxberg_config["host"]
                        network["explorer"] = bloxberg_config["explorer"]

            if not is_bloxberg_added:
                _config["networks"].append(bloxberg_config)
                _config["networks"].append(bloxberg_config_core)

    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=ind, sequence=ind, offset=bsi)
    with open(fn, "w") as fp:
        yaml.dump(config_data, fp)


def main():
    fn = Path.home() / ".brownie" / "network-config.yaml"
    add_bloxberg_config(fn)


if __name__ == "__main__":
    main()
