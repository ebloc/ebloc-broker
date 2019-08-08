#!/usr/bin/env python3

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from random import randint
from os.path import expanduser
import lib
from test.func import testFunc

home = expanduser("~")
path = os.getcwd()
# Definitions =============================================
providerID    = '0x57b60037b82154ec7149142c606ba024fbb0f991'
testType     = 'gdrive';
readTest     = 'hashOutput.txt'
cacheType    = lib.cacheType.private
# =========================================================
def log(strIn):
   print(strIn)
   txFile = open(path + '/clientOutput.txt', 'a')
   txFile.write( strIn + "\n" )
   txFile.close()

testFunc(path, readTest, testType, providerID, cacheType)
