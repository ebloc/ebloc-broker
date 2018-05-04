#!/usr/bin/python
import sys, os, subprocess, math
from subprocess import call
from os      import listdir
from os.path import isfile, join
import time
import datetime
from random import randint

sys.path.insert(0, '/home/prc/eBlocBroker/test')
from func import testFunc

path               = os.getcwd();
os.environ['path'] = path;

def contractCall( val ):
   return os.popen( val + "| node").read().replace("\n", "").replace(" ", "");

def log(strIn):
   print( strIn )
   txFile     = open(path + '/clientOutput.txt', 'a'); 
   txFile.write( strIn + "\n" ); 
   txFile.close();

header     = "var mylib = require('" + "/home/prc/eBlocBroker/eBlocBrokerHeader.js')";  os.environ['header']     = header;

cluster_id   = "0xe056d08f050503c1f068dc81fc7f7b705fc2c503";
readTest     = 'hashOutput.txt';
testType     = 'ipfsMiniLock';
workloadTest = "test_DAS2-fs1-2003-1.swf";
os.environ['miniLockId'] = "jj2Fn8St9tzLeErBiXA6oiZatnDwJ2YrnLY3Uyn4msD8k"
os.environ['cluster_id'] = cluster_id

# ==================================================================================================
testFunc(path, readTest, workloadTest, testType, cluster_id);
