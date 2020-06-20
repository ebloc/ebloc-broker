#!/usr/bin/env python3

import os
from os.path import expanduser
from test.func import testFunc

import owncloud

import lib

home = expanduser("~")
path = os.getcwd()
# definitions =============================================
providerID = "0x57b60037b82154ec7149142c606ba024fbb0f991"
testType = "gdrive"
readTest = "hashOutput.txt"
cacheType = lib.cacheType.private
# =========================================================
def log(strIn):
    print(strIn)
    txFile = open(path + "/clientOutput.txt", "a")
    txFile.write(strIn + "\n")
    txFile.close()


testFunc(path, readTest, testType, providerID, cacheType)
