#!/usr/bin/python

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from random import randint

path = os.getcwd(); os.environ['path'] = path;

def contractCall( val ):
      return os.popen( val + "| node").read().replace("\n", "").replace(" ", "");
    
counter = 0;
itemsToScan = 150;
hashesFile = open(path + '/hashOutput.txt', 'w+')
commentStr = "QmQANSjxQaziHPdMuj37LC53j65cVtXXwQYvu8GxJCPFJE"; # Dummy hash string

with open(path + "/nasa.txt") as test:
    for line in test:
        f = open(path + '/ipfs/run.sh', 'w+')
        lineIn = line.split(" ");

        if ((int(lineIn[1]) - int(lineIn[0])) > 60 ):
           print( "Time to take in seconds: "  + str(int(lineIn[1]) - int(lineIn[0])) )
           print( "CoreNum: "  + str(int(lineIn[2])) )
           print(line)

           with open(path + "/ipfs/run_temp.sh") as ff:
              for line in ff:
                 f.write(line);

           commentStr = str(random.getrandbits(128)) # Generates Random Hash
           print(commentStr)

           f.write("sleep " + str(int(lineIn[1]) - int(lineIn[0])) + "\n");
           f.write("#" + commentStr + "\n"); # Add random line to create different hash
           f.write("echo completed " + str(int(lineIn[1]) - int(lineIn[0])) + " > " + commentStr + ".txt\n"); #add random line to create different hash.
           f.write("echo completed " + str(int(lineIn[1]) - int(lineIn[0])) + " > completed.txt\n" ); #add random line to create different hash.
           f.close();

           #ipfsHash = os.popen( 'IPFS_PATH="/home/prc/.ipfs"; export IPFS_PATH; ipfs add -r /home/prc/testIpfs/ipfs' ).read();
           #ipfsHash = ipfsHash.split("\n");
           #commentStr = ipfsHash[len(ipfsHash) - 2].split(" ")[1];
           #print( "HASH: " + commentStr ); # lineNumber -> hash olarak kaydet.

           copyIntoSharePath = path + "/oc" + "/" + commentStr;
           os.environ['copyIntoSharePath'] = copyIntoSharePath;

           if not os.path.isdir(copyIntoSharePath):
              os.makedirs(copyIntoSharePath)

           os.popen("cp -a /home/prc/multiple/eudat/ipfs/* $copyIntoSharePath")

           hashesFile.write(commentStr + " " + str(int(lineIn[1]) - int(lineIn[0])) + " " + str(int(lineIn[2])) +"\n"); ##
           if (counter == itemsToScan):
              break;
           print(counter)
           counter += 1;
hashesFile.close();
#}

print('Sharing files now...')
print(os.popen('python $path/shareOwnCloud.py').read());
