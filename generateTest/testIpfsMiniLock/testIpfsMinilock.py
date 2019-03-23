#!/usr/bin/env python3

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from random import randint
from os.path import expanduser
home = expanduser("~")

sys.path.insert(0, home + '/eBlocBroker/')
sys.path.insert(0, home + '/eBlocBroker/test')
import lib
from func import testFunc

path = os.getcwd()
# Definitions =============================================
clusterID    = '0x398bd2a9a39637884b49b2b0930de7d83eb08a8e' #googleInstance-1
testType     = 'ipfsMiniLock';
readTest     = 'hashOutput.txt'
cacheType    = lib.cacheType.ipfs
# =========================================================
def log(strIn):
   print(strIn)
   txFile = open(path + '/clientOutput.txt', 'a')
   txFile.write( strIn + "\n" )
   txFile.close()
   
testFunc(path, readTest, testType, clusterID, cacheType)
