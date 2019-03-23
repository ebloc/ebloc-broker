#!/usr/bin/env python3

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys, subprocess
from os.path import expanduser
from random import randint
home = expanduser("~")
sys.path.insert(0, home + '/eBlocBroker')
from lib_owncloud import singleFolderShare, eudatInitializeFolder
path = os.getcwd()
os.environ['path'] = path

mlckPass="gene threatens achieving ireland stalkers spoiling preoccupying"
os.environ['clusterMiniLockId'] = "EyJ6jk9GuZkYAqUZ5UsrZ3RsvQ7cLk2XEzLXeVegyEBSQ"
flag        = 0
counter     = 0
itemsToScan = 100 + 1
hashesFile = open(path + '/hashOutput.txt', 'w+')
with open(path + "/../test_DAS2-fs1-2003-1.swf") as test:
    for line in test:
        f = open('../ipfs/run.sh', 'w+')
        lineIn = line.split(" ")
        if int(lineIn[1]) - int(lineIn[0]) > 60 and int(lineIn[2]) != 0:
            print("Time to take in seconds: "  + str(int(lineIn[1]) - int(lineIn[0])))
            print("CoreNum: "  + str(int(lineIn[2])))
            print(line)
            with open("../ipfs/run_temp.sh") as ff:
                for line in ff:
                    f.write(line)

            randomHash = str(random.getrandbits(128)) + str(random.getrandbits(128))
            f.write("sleep " + str(int(lineIn[1]) - int(lineIn[0])) + "\n")
            f.write("#" + randomHash + "\n") # Add random line to create different hash
            f.write("echo completed " + str(int(lineIn[1]) - int(lineIn[0])) + " > completed.txt\n" )
            f.close()
            encrypyFolderPath = "/home/prc/eBlocBroker/generateTest/ipfs";
            os.chdir(encrypyFolderPath)
            p1 = subprocess.Popen(['find', '.', '-print0'], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(['sort', '-z'], stdin=p1.stdout, stdout=subprocess.PIPE, env={'LC_ALL': 'C'})
            p1.stdout.close()
            p3 = subprocess.Popen(['tar', '--absolute-names', '--no-recursion', '--null', '-T', '-', '-zcvf', '../ipfs.tar.gz'],
                                  stdin=p2.stdout,stdout=subprocess.PIPE, env={'GZIP': '-n'})
            p2.stdout.close()
            p3.communicate()
            
            os.popen('mlck encrypt -f ../ipfs.tar.gz $clusterMiniLockId --passphrase="'+ mlckPass + '"').read()
            fileTShare = "../ipfs.tar.gz.minilock"
            os.environ['fileTShare'] = fileTShare
            tarHash = os.popen('md5sum $fileTShare | awk \'{print $1}\'').read()
            tarHash = os.popen('md5sum $fileTShare').read()
            tarHash = tarHash.split(" ")[0];

            print('SourecodeHash=' + tarHash)
            ipfsHash = os.popen('ipfs add ../ipfs.tar.gz.minilock').read();
            ipfsHash = ipfsHash.split(" ")[1];
            print('ipfsHash=' + ipfsHash)
            if flag == 1:
                hashesFile.write(" " + str(int(lineIn[0])-startTimeTemp) + '\n')

            flag = 1
            startTimeTemp = int(lineIn[0])
            print("Shared Job=" + str(counter))
            counter += 1
            if counter == itemsToScan:
                break

            hashesFile.write(ipfsHash + " " + str(int(lineIn[1]) - int(lineIn[0])) + " " + str(int(lineIn[2])) + " " +
                             str(int(lineIn[0])) + " " + str(int(lineIn[1])) + " " + tarHash)

hashesFile.close()
print('\nDONE.')
