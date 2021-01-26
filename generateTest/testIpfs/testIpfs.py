#!/usr/bin/env python3

import datetime
import getpass
import hashlib
import math
import os
import random
import sys
import time
from os.path import expanduser
from random import randint
from test.func import testFunc

import owncloud

import lib

home = expanduser("~")
path = os.getcwd()
# definitions ===========================================
providerID = "0x2fe8fb59f6e24703f8732fcd38f4ac9e8f56d8aa"  # googleInstance-3
testType = "ipfs"
readTest = "hashOutput.txt"
cacheType = lib.cacheType.ipfs
# =======================================================
def log(strIn):
    print(strIn)
    txFile = open(path + "/clientOutput.txt", "a")
    txFile.write(strIn + "\n")
    txFile.close()


testFunc(path, readTest, testType, providerID, cacheType)
