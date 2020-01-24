#!/usr/bin/env python3

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from random import randint
from os.path import expanduser
import lib
from test.func import testFunc

home = expanduser("~")
path = os.getcwd()
# Definitions =============================================
providerID = "0x2fe8fb59f6e24703f8732fcd38f4ac9e8f56d8aa"  # googleInstance-3
testType = "ipfs"
readTest = "hashOutput.txt"
cacheType = lib.cacheType.ipfs
# =========================================================
def log(strIn):
    print(strIn)
    txFile = open(path + "/clientOutput.txt", "a")
    txFile.write(strIn + "\n")
    txFile.close()


testFunc(path, readTest, testType, providerID, cacheType)
