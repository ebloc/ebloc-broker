#!/usr/bin/env python3

import os
import random
import subprocess
from os.path import expanduser

from broker.utils import generate_md5sum

home = expanduser("~")

path = os.getcwd()
os.environ["path"] = path
flag = 0
itemsToScan = 100 + 1
hashesFile = open(path + "/hashOutput.txt", "w+")
with open(path + "/../test_DAS2-fs1-2003-1.swf") as test:
    for idx, line in enumerate(test):
        f = open("../ipfs/run.sh", "w+")
        lineIn = line.split(" ")
        if int(lineIn[1]) - int(lineIn[0]) > 60 and int(lineIn[2]) != 0:
            print("Time to take in seconds: " + str(int(lineIn[1]) - int(lineIn[0])))
            print("CoreNum: " + str(int(lineIn[2])))
            print(line)
            with open("../ipfs/run_temp.sh") as ff:
                for line in ff:
                    f.write(line)

            randomHash = str(random.getrandbits(128)) + str(random.getrandbits(128))
            f.write("sleep " + str(int(lineIn[1]) - int(lineIn[0])) + "\n")
            f.write("#" + randomHash + "\n")  # add random line to create different hash
            f.write("echo completed " + str(int(lineIn[1]) - int(lineIn[0])) + " > completed.txt\n")
            f.close()
            ipfsHash = os.popen("ipfs add -r ../ipfs").read()
            ipfsHash = ipfsHash.split("\n")
            ipfsHash = ipfsHash[len(ipfsHash) - 2].split(" ")[1]

            folderToShare = "../ipfs"
            tar_hash = generate_md5sum(folderToShare)
            tar_hash = tar_hash.split(" ", 1)[0]
            print("SourecodeHash=" + tar_hash)
            print("ipfsHash=" + ipfsHash)
            startTimeTemp = 0
            if flag == 1:
                hashesFile.write(" " + str(int(lineIn[0]) - startTimeTemp) + "\n")

            flag = 1
            startTimeTemp = int(lineIn[0])
            print("Shared Job=" + str(idx))
            if idx == itemsToScan - 1:
                break

            hashesFile.write(
                ipfsHash
                + " "
                + str(int(lineIn[1]) - int(lineIn[0]))
                + " "
                + str(int(lineIn[2]))
                + " "
                + str(int(lineIn[0]))
                + " "
                + str(int(lineIn[1]))
                + " "
                + tar_hash
            )

hashesFile.close()
print("\nDONE.")
subprocess.run(["cp", path + "/hashOutput.txt", path + "/hashOutput_temp.txt"])
