#!/usr/bin/env python3

import os
import random
import subprocess
from os.path import expanduser

home = expanduser("~")
path = os.getcwd()
os.environ["path"] = path

mlckPass = "gene threatens achieving ireland stalkers spoiling preoccupying"
os.environ["provider_minilock_id"] = "EyJ6jk9GuZkYAqUZ5UsrZ3RsvQ7cLk2XEzLXeVegyEBSQ"
flag = 0
itemsToScan = 100 + 1
hashesFile = open(path + "/hashOutput.txt", "w+")
with open(path + "/../test_DAS2-fs1-2003-1.swf") as test:
    for idx, line in enumerate(test):
        f = open("../ipfs/run.sh", "w+")
        lineIn = line.split(" ")
        if int(lineIn[1]) - int(lineIn[0]) > 60 and int(lineIn[2]) != 0:
            print("Time to take in seconds: " + str(int(lineIn[1]) - int(lineIn[0])))
            print(f"core_num={int(lineIn[2])}")
            print(line)
            with open("../ipfs/run_temp.sh") as ff:
                for line in ff:
                    f.write(line)

            randomHash = str(random.getrandbits(128)) + str(random.getrandbits(128))
            f.write("sleep " + str(int(lineIn[1]) - int(lineIn[0])) + "\n")
            f.write("#" + randomHash + "\n")  # add random line to create different hash
            f.write("echo completed " + str(int(lineIn[1]) - int(lineIn[0])) + " > completed.txt\n")
            f.close()
            encrypyFolderPath = "/home/prc/eBlocBroker/generateTest/ipfs"
            os.chdir(encrypyFolderPath)
            p1 = subprocess.Popen(["find", ".", "-print0"], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(
                ["sort", "-z"],
                stdin=p1.stdout,
                stdout=subprocess.PIPE,
                env={"LC_ALL": "C"},
            )
            p1.stdout.close()

            cmd = [
                "tar",
                "--absolute-names",
                "--no-recursion",
                "--null",
                "-T",
                "-",
                "-zcvf",
                "../ipfs.tar.gz",
            ]
            p3 = subprocess.Popen(cmd, stdin=p2.stdout, stdout=subprocess.PIPE, env={"GZIP": "-n"})
            p2.stdout.close()
            p3.communicate()

            os.popen('mlck encrypt -f ../ipfs.tar.gz $provider_minilock_id --passphrase="' + mlckPass + '"').read()
            fileTShare = "../ipfs.tar.gz.minilock"
            os.environ["fileTShare"] = fileTShare
            tar_hash = os.popen("md5sum $fileTShare | awk '{print $1}'").read()
            tar_hash = os.popen("md5sum $fileTShare").read()
            tar_hash = tar_hash.split(" ")[0]

            print("SourecodeHash=" + tar_hash)
            ipfsHash = os.popen("ipfs add ../ipfs.tar.gz.minilock").read()
            ipfsHash = ipfsHash.split(" ")[1]
            print("ipfsHash=" + ipfsHash)
            # if flag == 1:
            #     hashesFile.write(" " + str(int(lineIn[0]) - startTimeTemp) + "\n")

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
