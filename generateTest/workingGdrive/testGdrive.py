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

header     = "var mylib = require('" + "/home/prc/eBlocBroker/eBlocBrokerHeader.js')"; os.environ['header'] = header;

# Definitions ===========================================
testType     = 'gdrive';
workloadTest = 'nasa.txt';
readTest     = 'hashOutput.txt';
clusterID    = "0xf2129928bd1e6f4aa1ad131a37db2e55810cbbff"; #Tetam
# clusterID    = "0xf20b4c9068a3945ce5cd73d50fdabbf04412e421"; #GoogleInstance
os.environ['clusterID'] = clusterID;
# =======================================================

testFunc(path, readTest, workloadTest, testType, clusterID);
