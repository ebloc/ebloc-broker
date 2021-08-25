#!/usr/bin/env python3

import json
import os

from config import env
from dotenv import load_dotenv
from utils import read_json

# load .env from the given path
load_dotenv(os.path.join(f"{env.HOME}/.ebloc-broker/", ".env"))


def add_element(data, key, elementToAdd):
    data[key] = elementToAdd


def remove_element(data, elementToRemove):
    for element in list(data):
        if elementToRemove in element:
            del data[elementToRemove]


f = os.getenv("LOG_PATH") + "/" + "cachingRecord.json"
print(f)

if not os.path.isfile(f):
    data = {}
else:
    try:
        data = read_json(f)
    except:
        pass

add_element(data, "jobKey", ["local", "userName", "timestamp", "keepTime"])
add_element(data, "ipfsHash", "timestamp")

with open("data.json", "w") as outfile:
    json.dump(data, outfile)

if "jobKey" in data:
    print(data["jobKey"][0])
    print(data["jobKey"])

remove_element(data, "ipfsHash")
with open(f, "w") as data_file:
    data = json.dump(data, data_file)
