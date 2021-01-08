#!/usr/bin/env python3

import os
from os.path import expanduser
from test.func import testFunc

import lib

home = expanduser("~")
path = os.getcwd()

provider_id = "0x2fe8fb59f6e24703f8732fcd38f4ac9e8f56d8aa"  # googleInstance-3
testType = "ipfs"
readTest = "hashOutput.txt"
cacheType = lib.cacheType.ipfs


def log(str_in):
    print(str_in)
    txFile = open(path + "/clientOutput.txt", "a")
    txFile.write(str_in + "\n")
    txFile.close()


testFunc(path, readTest, testType, provider_id, cacheType)
