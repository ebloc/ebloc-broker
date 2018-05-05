#!/usr/bin/python

import sys, os, subprocess, math, sys
from subprocess import call
from os      import listdir
from os.path import isfile, join
import time
import datetime
from random import randint

sys.path.insert(0, '/home/prc/eBlocBroker/test');
from func import testFunc

def contractCall( val ):
   return os.popen( val + "| node").read().replace("\n", "").replace(" ", "");

def log(strIn):
   print(strIn)
   txFile     = open(path + '/clientOutput.txt', 'a'); 
   txFile.write(strIn + "\n"); 
   txFile.close();

path =os.getcwd(); os.environ['path'] = path;
header     = "var mylib = require('" + "/home/prc/eBlocBroker/eBlocBrokerHeader.js')";  os.environ['header']     = header;

testType     = 'ipfs';
workloadTest = "test_DAS2-fs1-2003-1.swf";
readTest     = 'hashOutput.txt';
clusterID    = "0xcc8de90b4ada1c67d68c1958617970308e4ee75e";
os.environ['clusterID'] = clusterID

testFunc(path, readTest, workloadTest, testType, clusterID);
