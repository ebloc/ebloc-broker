#!/usr/bin/env python3

import json
import os

from dotenv import load_dotenv

from broker._utils.tools import read_json
from broker.config import env

# load .env from the given path
load_dotenv(os.path.join(f"{env.HOME}/.ebloc-broker/", ".env"))


def addElement(data, key, elementToAdd):
    data[key] = elementToAdd


def remove_element(data, element_to_remove):
    for element in list(data):
        if element_to_remove in element:
            del data[element_to_remove]


fn = env.LOG_PATH + "/" + "cachingRecord.json"
print(fn)
if not os.path.isfile(fn):
    data = {}
else:
    try:
        data = read_json(fn)
    except:
        pass

addElement(data, "jobKey", ["local", "userName", "timestamp", "keepTime"])
addElement(data, "ipfsHash", "timestamp")

with open("data.json", "w") as outfile:
    json.dump(data, outfile)

if "jobKey" in data:
    print(data["jobKey"][0])
    print(data["jobKey"])

remove_element(data, "ipfsHash")
with open(fn, "w") as data_file:
    json.dump(data, data_file)
