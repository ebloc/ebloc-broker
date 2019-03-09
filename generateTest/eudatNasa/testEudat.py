#!/usr/bin/env python3

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from os.path import expanduser
from random import randint
home = expanduser("~")

sys.path.insert(0, home + '/eBlocBroker/test')
from func import testFunc

path = os.getcwd()
os.environ['path'] = path

def log(strIn):
   print( strIn )
   txFile     = open( '/home/prc/multiple/nasEudat' + '/clientOutput.txt', 'a');
   txFile.write( strIn + "\n" );
   txFile.close();

# Login to EUDAT account----------------------------------------
f = open(home + '/TESTS/password.txt', 'r'); # Password read from the file.
password = f.read().replace("\n", "").replace(" ", "")
f.close()
oc = owncloud.Client('https://b2drop.eudat.eu/')
oc.login('059ab6ba-4030-48bb-b81b-12115f531296', password)
#---------------------------------------------------------------
SHARE_PATH = home + "/oc"

# Definitions ===========================================
clusterID    = "0x4e4a0750350796164d8defc442a712b7557bf282"
testType     = 'eudat-nas';
workloadTest = 'nasa.txt';
readTest     = 'hashOutput.txt';
# ==================================================================================================
testFunc(path, readTest, workloadTest, testType, clusterID);
                  
'''
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
'''
