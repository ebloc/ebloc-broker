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
   print(strIn)
   txFile     = open(path + '/clientOutput.txt', 'a'); 
   txFile.write( strIn + "\n" ); 
   txFile.close();

header     = "var mylib = require('" + "/home/prc/eBlocBroker/eBlocBrokerHeader.js')";  os.environ['header']     = header;

readTest    = 'hashOutput.txt';
input('> Are you sure want to overwrite ' + readTest + '?');
counter     = 0;
itemsToScan = 80;
hashesFile  = open(path + '/' + readTest, 'w+')
commentStr  = "QmQANSjxQaziHPdMuj37LC53j65cVtXXwQYvu8GxJCPFJE"; #dummy hash string.

os.environ['clusterMiniLockId'] = "SjPmN3Fet4bKSBJAutnAwA15ct9UciNBNYo1BQCFiEjHn";
with open(path + "/test_DAS2-fs1-2003-1.swf") as test: #{
    for line in test:
        f = open(path + '../ipfs/run.sh', 'w+')
        lineIn = line.split(" ");

        if ((int(lineIn[1]) - int(lineIn[0])) > 60 ):
           print( "----------------------------------------" )
           print( "Scanned Item: " + str(counter) )
           print( "Time to take in seconds: "  + str(int(lineIn[1]) - int(lineIn[0])) )
           print( "CoreNum: "  + str(int(lineIn[2])) )
           print(line)

           with open(path + "../ipfs/run_temp.sh") as ff:
              for line in ff:
                 f.write(line);
                 
           f.write("sleep " + str(int(lineIn[1]) - int(lineIn[0])) + "\n");
           f.write("#" + commentStr + "\n"); #add random line to create different hash.
           f.write("echo completed " + str(int(lineIn[1]) - int(lineIn[0])) + " > " + commentStr + ".txt\n"); #add random line to create different hash.
           f.write("echo completed " + str(int(lineIn[1]) - int(lineIn[0])) + " > completed.txt\n" ); #add random line to create different hash.
           f.close();

           encrypyFolderPath = path + "../ipfs";
           os.chdir(encrypyFolderPath)
           os.environ['encrypyFolderPath'] = encrypyFolderPath
           os.popen('tar -P -cvzf $path/../ipfs.tar.gz .').read();
           os.popen('mlck encrypt -f $path/../ipfs.tar.gz $clusterMiniLockId --passphrase="gene threatens achieving ireland stalkers spoiling preoccupying"').read();
           ipfsHash = os.popen( 'ipfs add $path/../ipfs.tar.gz.minilock' ).read();
           ipfsHash = ipfsHash.split(" ")[1];
           print(ipfsHash)
           commentStr = ipfsHash;
           hashesFile.write(commentStr + " " + str(int(lineIn[1]) - int(lineIn[0])) + " " + str(int(lineIn[2])) +"\n");

           if(counter == itemsToScan):
              break;
           counter += 1;
#}

hashesFile.close();
sys.exit();


