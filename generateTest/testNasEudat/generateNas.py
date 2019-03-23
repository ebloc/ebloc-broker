#!/usr/bin/env python3

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from os.path import expanduser
from random import randint
home = expanduser("~")
sys.path.insert(0, home + '/eBlocBroker')
from lib_owncloud import singleFolderShare, eudatInitializeFolder
path = os.getcwd()
os.environ['path'] = path

# Login to EUDAT account----------------------------------------
f = open(home + '/TESTS/password.txt', 'r') # Password read from the file.
password = f.read().replace("\n", "").replace(" ", "")
f.close()
oc = owncloud.Client('https://b2drop.eudat.eu/')
oc.login('059ab6ba-4030-48bb-b81b-12115f531296', password)
#---------------------------------------------------------------
startTime   = 1
counter     = 0
itemsToScan = 100 + 1
hashesFile = open(path + '/hashOutput.txt', 'w+')
coreLimit   = 7200 #120*60 (2 hours money is paid)
counter = 0
while True:
    if counter > itemsToScan:
        break

    f = open('ipfs/run.sh', 'w+')
    with open("ipfs/run_temp.sh") as ff:
        for line in ff:
            f.write(line)

    testId  = randint(0, 3)
    coreNum = 1 # randint(1, 2)
    if testId == 0:
        f.write("make bt CLASS=B\n")
        f.write("bin/bt.B.x inputbt.data")
    elif testId == 1:
        f.write("make sp CLASS=B\n")
        f.write("bin/sp.B.x inputsp.data")
    elif testId == 2:
        f.write("make ua CLASS=B\n")
        f.write("bin/ua.B.x inputua.data")
    elif testId == 3:
        f.write("make lu CLASS=B\n")
        f.write("bin/lu.B.x inputlu.data")

    f.close()
    tarHash = eudatInitializeFolder('ipfs', oc)
    time.sleep(1)
    print(singleFolderShare(tarHash, oc))
    print("Shared Job#" + str(counter))
    sleepTime = randint(300, 600)
    hashesFile.write(tarHash + " " + str(coreLimit) + " " + str(coreNum) + " " + str(startTime) + " " +
                     str(startTime + coreLimit) + " " + tarHash + " " + str(sleepTime) + "\n")
    startTime += sleepTime
    counter   += 1

'''
    if testId == 0:
        f.write("make bt CLASS=B\n")
        f.write("mpirun -n " + str(coreNum) + " bin/bt.B.x inputbt.data")
    elif testId == 1:
        f.write("make sp CLASS=B\n")
        f.write("mpirun -n " + str(coreNum) + " bin/sp.B.x inputsp.data")
    elif testId == 2:
        f.write("make ua CLASS=B\n")
        f.write("mpirun -n " + str(coreNum) + " bin/ua.B.x inputua.data")
    elif testId == 3:
        f.write("make lu CLASS=B\n")
        f.write("mpirun -n " + str(coreNum) + " bin/lu.B.x inputlu.data")
'''    
