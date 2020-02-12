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
# Definitions =============================================
providerID = "0x398bd2a9a39637884b49b2b0930de7d83eb08a8e"  # googleInstance-1
testType = "ipfsMiniLock"
readTest = "hashOutput.txt"
cacheType = lib.cacheType.ipfs
# =========================================================
def log(strIn):
    print(strIn)
    txFile = open(path + "/clientOutput.txt", "a")
    txFile.write(strIn + "\n")
    txFile.close()


testFunc(path, readTest, testType, providerID, cacheType)
