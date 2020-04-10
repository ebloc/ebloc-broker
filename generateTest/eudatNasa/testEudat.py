#!/usr/bin/env python3

import os
from os.path import expanduser
from test.func import testFunc

import owncloud

import lib


def log(strIn):
    print(strIn)
    txFile = open(path + "/clientOutput.txt", "a")
    txFile.write(strIn + "\n")
    txFile.close()


home = expanduser("~")
path = os.getcwd()

providerID = "0x4e4a0750350796164d8defc442a712b7557bf282"
testType = "eudat-nasa"
readTest = "hashOutput.txt"
cacheType = lib.cacheType.private

# login to EUDAT account----------------------------------------
f = open(f"{home}/TESTS/password.txt", "r")  # password read from the file
password = f.read().strip()
f.close()
oc = owncloud.Client("https://b2drop.eudat.eu/")
oc.login("059ab6ba-4030-48bb-b81b-12115f531296", password)
# ---------------------------------------------------------------
testFunc(path, readTest, testType, providerID, cacheType)
