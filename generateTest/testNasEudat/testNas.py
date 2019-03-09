#!/usr/bin/python

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from os.path import expanduser
from random import randint
sys.path.insert(0, '/home/prc/eBlocBroker/test')
from func import testFunc

path = os.getcwd(); os.environ['path'] = path;
home = expanduser("~")

def contractCall( val ):
   return os.popen( val + "| node").read().replace("\n", "").replace(" ", "");

def log(strIn):
   print( strIn )
   txFile     = open( '/home/prc/multiple/nasEudat' + '/clientOutput.txt', 'a'); 
   txFile.write( strIn + "\n" ); 
   txFile.close();

# Login to EUDAT account----------------------------------------
f = open(path+"/password.txt", 'r'); # Password read from the file. 
password = f.read().replace("\n", "").replace(" ", "")
f.close()
oc = owncloud.Client('https://b2drop.eudat.eu/')
oc.login('alper.alimoglu@boun.edu.tr', password )
#---------------------------------------------------------------
SHARE_PATH = home + "/oc"
header     = "var mylib = require('" + "/home/prc/eBlocBroker/eBlocBrokerHeader.js')"
os.environ['header'] = header

# Definitions ===========================================
clusterID    = "0x4e4a0750350796164d8defc442a712b7557bf282"
os.environ['clusterID'] = clusterID
testType     = 'eudat-nas';
workloadTest = 'nasa.txt';
readTest     = 'hashOutput.txt';
# ==================================================================================================
testFunc(path, readTest, workloadTest, testType, clusterID);
