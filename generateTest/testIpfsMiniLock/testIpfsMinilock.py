#!/usr/bin/env python3

import os
from test.func import testFunc

import lib

path = os.getcwd()

providerID = "0x398bd2a9a39637884b49b2b0930de7d83eb08a8e"  # googleInstance-1
testType = "ipfsMiniLock"
readTest = "hashOutput.txt"
cacheType = lib.cacheType.ipfs


def log(strIn):
    print(strIn)
    txFile = open(path + "/clientOutput.txt", "a")
    txFile.write(strIn + "\n")
    txFile.close()


testFunc(path, readTest, testType, providerID, cacheType)
