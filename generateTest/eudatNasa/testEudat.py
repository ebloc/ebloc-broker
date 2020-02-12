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
providerID = "0x4e4a0750350796164d8defc442a712b7557bf282"
testType = "eudat-nasa"
readTest = "hashOutput.txt"
cacheType = lib.cacheType.private
# =========================================================
def log(strIn):
    print(strIn)
    txFile = open(path + "/clientOutput.txt", "a")
    txFile.write(strIn + "\n")
    txFile.close()


# Login to EUDAT account----------------------------------------
f = open(home + "/TESTS/password.txt", "r")  # Password read from the file.
password = f.read().replace("\n", "").replace(" ", "")
f.close()
oc = owncloud.Client("https://b2drop.eudat.eu/")
oc.login("059ab6ba-4030-48bb-b81b-12115f531296", password)
# ---------------------------------------------------------------
testFunc(path, readTest, testType, providerID, cacheType)
