#!/usr/bin/python

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from random import randint
sys.path.insert(0, '/home/prc/eBlocBroker/test')
from func import testFunc

path =os.getcwd(); os.environ['path'] = path;

def contractCall( val ):
   return os.popen( val + "| node").read().replace("\n", "").replace(" ", "");

def log(strIn):
   print(strIn)
   txFile  = open(path + '/clientOutput.txt', 'a'); 
   txFile.write(strIn + "\n"); 
   txFile.close();

header = "var mylib = require('" + "/home/prc/eBlocBroker/eBlocBrokerHeader.js')";
os.environ['header'] = header;

# Definitions =============================================
testType     = 'eudat';
workloadTest = 'nasa.txt';
readTest     = 'hashOutput.txt';
clusterID    = "0x4e4a0750350796164d8defc442a712b7557bf282";
os.environ['clusterID'] = clusterID;
# ==========================================================
testFunc(path, readTest, workloadTest, testType, clusterID);
