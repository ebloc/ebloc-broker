#!/usr/bin/python

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from random import randint
sys.path.insert(0, '/home/prc/eBlocBroker/test')
from func import testFunc

path = os.getcwd(); os.environ['path'] = path;

def contractCall( val ):
   return os.popen( val + "| node").read().replace("\n", "").replace(" ", "");

def log(strIn):
   print( strIn )
   txFile     = open( '/home/prc/multiple/nasEudat' + '/clientOutput.txt', 'a'); 
   txFile.write( strIn + "\n" ); 
   txFile.close();

# Login to EUDAT account----------------------------------------
f = open( path+"/password.txt", 'r'); # Password read from the file. 
password = f.read().replace("\n", "").replace(" ", "")
f.close()
oc = owncloud.Client('https://b2drop.eudat.eu/')
oc.login('alper.alimoglu@boun.edu.tr', password )
#---------------------------------------------------------------
SHARE_PATH=path+"/oc"
header     = "var mylib = require('" + "/home/prc/eBlocBroker/eBlocBrokerHeader.js')"; os.environ['header'] = header;

# Definitions ===========================================
clusterID = "0xda1e61e853bb8d63b1426295f59cb45a34425b63"; os.environ['clusterID'] = clusterID;
testType     = 'eudat-nas';
workloadTest = 'nasa.txt';
readTest     = 'hashOutput.txt';
# ==================================================================================================
testFunc(path, readTest, workloadTest, testType, clusterID);
