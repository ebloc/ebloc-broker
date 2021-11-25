#!/usr/bin/env python3

import itertools
import os
import subprocess
import time
from os.path import expanduser
from random import randint

import libs.eudat as eudat
import owncloud

home = expanduser("~")

path = os.getcwd()
os.environ["path"] = path

# login to EUDAT account----------------------------------------
f = open(home + "/TESTS/password.txt", "r")  # password read from the file
password = f.read().replace("\n", "").replace(" ", "")
f.close()
oc = owncloud.Client("https://b2drop.eudat.eu/")
oc.login("059ab6ba-4030-48bb-b81b-12115f531296", password)
# ---------------------------------------------------------------
startTime = 1

itemsToScan = 100 + 1
hashesFile = open(path + "/hashOutput.txt", "w+")
coreLimit = 7200  # 120*60 (2 hours money is paid)

for idx in itertools.count(0):
    if idx > itemsToScan:
        break

    f = open("ipfs/run.sh", "w+")
    with open("ipfs/run_temp.sh") as ff:
        for line in ff:
            f.write(line)

    test_id = randint(0, 3)
    coreNum = 1  # randint(1, 2)
    if test_id == 0:
        f.write("make bt CLASS=B\n")
        f.write("bin/bt.B.x inputbt.data")
    elif test_id == 1:
        f.write("make sp CLASS=B\n")
        f.write("bin/sp.B.x inputsp.data")
    elif test_id == 2:
        f.write("make ua CLASS=B\n")
        f.write("bin/ua.B.x inputua.data")
    elif test_id == 3:
        f.write("make lu CLASS=B\n")
        f.write("bin/lu.B.x inputlu.data")

    f.close()
    tarHash = eudat.initialize_folder("ipfs", oc)
    time.sleep(1)
    print(eudat.share_single_folder(tarHash, oc))
    print(f"Shared Job#{idx}")
    sleepTime = randint(300, 600)
    hashesFile.write(
        tarHash
        + " "
        + str(coreLimit)
        + " "
        + str(coreNum)
        + " "
        + str(startTime)
        + " "
        + str(startTime + coreLimit)
        + " "
        + tarHash
        + " "
        + str(sleepTime)
        + "\n"
    )
    startTime += sleepTime

subprocess.run(["cp", path + "/hashOutput.txt", path + "/hashOutput_temp.txt"])

"""
    if test_id == 0:
        f.write("make bt CLASS=B\n")
        f.write("mpirun -n " + str(coreNum) + " bin/bt.B.x inputbt.data")
    elif test_id == 1:
        f.write("make sp CLASS=B\n")
        f.write("mpirun -n " + str(coreNum) + " bin/sp.B.x inputsp.data")
    elif test_id == 2:
        f.write("make ua CLASS=B\n")
        f.write("mpirun -n " + str(coreNum) + " bin/ua.B.x inputua.data")
    elif test_id == 3:
        f.write("make lu CLASS=B\n")
        f.write("mpirun -n " + str(coreNum) + " bin/lu.B.x inputlu.data")
"""
