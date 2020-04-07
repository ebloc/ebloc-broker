#!/usr/bin/env python3

import os
import random
import subprocess
import time
from os.path import expanduser

import owncloud

import libs.eudat as eudat

home = expanduser("~")
path = os.getcwd()

# TODO: carry it into a function
# Login to EUDAT account----------------------------------------
f = open(f"{home}/TESTS/password.txt", "r")  # Password read from the file.
password = f.read().strip()
f.close()
oc = owncloud.Client("https://b2drop.eudat.eu/")
oc.login("059ab6ba-4030-48bb-b81b-12115f531296", password)
# ---------------------------------------------------------------

flag = 0
itemsToScan = 151
hashesFile = open(path + "/hashOutput.txt", "w+")
with open(path + "/../nasa.txt") as test:
    for idx, line in enumerate(test):
        f = open("ipfs/run.sh", "w+")
        lineIn = line.split(" ")
        if int(lineIn[1]) - int(lineIn[0]) > 60 and int(lineIn[2]) != 0:
            print("Time to take in seconds: " + str(int(lineIn[1]) - int(lineIn[0])))
            print("CoreNum: " + str(int(lineIn[2])))
            print(line)
            with open("ipfs/run_temp.sh") as ff:
                for line in ff:
                    f.write(line)

            randomHash = str(random.getrandbits(128)) + str(random.getrandbits(128))
            f.write("sleep " + str(int(lineIn[1]) - int(lineIn[0])) + "\n")
            f.write("#" + randomHash + "\n")  # Add random line to create different hash
            f.write("echo completed " + str(int(lineIn[1]) - int(lineIn[0])) + " > completed.txt\n")
            f.close()
            tarHash = eudat.initialize_folder("ipfs", oc)  # Should give folder name
            time.sleep(1)
            # After run.sh is update share the ipfs through eudat
            print(eudat.share_single_folder(tarHash, oc))
            if flag == 1:
                hashesFile.write(" " + str(int(lineIn[0]) - startTimeTemp) + "\n")

            flag = 1
            startTimeTemp = int(lineIn[0])
            print("Shared Job#" + str(idx))
            if idx == itemsToScan - 1:
                break

            hashesFile.write(
                tarHash
                + " "
                + str(int(lineIn[1]) - int(lineIn[0]))
                + " "
                + str(int(lineIn[2]))
                + " "
                + str(int(lineIn[0]))
                + " "
                + str(int(lineIn[1]))
                + " "
                + tarHash
            )

hashesFile.close()
print("\nFolders are created. Sharing files now...")
subprocess.run(["cp", path + "/hashOutput.txt", path + "/hashOutput_temp.txt"])

# -------------------------------------
# print(os.popen('python $path/shareOwnCloud.py').read())
# ipfsHash = os.popen( 'IPFS_PATH="/home/prc/.ipfs" export IPFS_PATH ipfs add -r /home/prc/testIpfs/ipfs' ).read()
# ipfsHash = ipfsHash.split("\n")
# tarHash = ipfsHash[len(ipfsHash) - 2].split(" ")[1]
# print( "HASH: " + tarHash )  # lineNumber -> hash olarak kaydet.
