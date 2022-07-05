#!/usr/bin/env python3

import json
import os
from contextlib import suppress

from broker._utils.tools import read_json
from broker.config import env


def add_element(data, key, elementToAdd):
    data[key] = elementToAdd


def remove_element(data, element_to_remove):
    for element in list(data):
        if element_to_remove in element:
            del data[element_to_remove]


def main():
    fn = env.LOG_PATH + "/" + "caching_record.json"
    if os.path.isfile(fn):
        with suppress(Exception):
            data = read_json(fn)
    else:
        data = {}

    add_element(data, "jobKey", ["local", "userName", "timestamp", "keepTime"])
    add_element(data, "ipfs_hash", "timestamp")
    with open("data.json", "w") as outfile:
        json.dump(data, outfile)

    if "jobKey" in data:
        print(data["jobKey"][0])
        print(data["jobKey"])

    remove_element(data, "ipfs_hash")
    with open(fn, "w") as data_file:
        json.dump(data, data_file)


if __name__ == "__main__":
    main()
