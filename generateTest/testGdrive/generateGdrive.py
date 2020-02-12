#!/usr/bin/env python3

import os
import random
import subprocess
from os.path import expanduser

from lib import compressFolder

home = expanduser("~")
path = os.getcwd()

providerToShare = "alper01234alper@gmail.com"
flag = 0
itemsToScan = 150 + 1
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

            folderToShare = "ipfs"
            tarHash = (
                subprocess.check_output(["../../scripts/generateMD5sum.sh", folderToShare]).decode("utf-8").strip()
            )
            tarHash = tarHash.split(" ", 1)[0]
            print("SourecodeHash=" + tarHash)

            os.environ["fileName"] = tarHash
            os.environ["providerToShare"] = "alper01234alper@gmail.com"

            tarHash = compressFolder(folderToShare)
            # subprocess.run(['cp', '-a', '../ipfs', '../' + tarHash])
            print("Uploading ...")
            # rclone copy ipfs remote:ipfs
            res = (
                subprocess.check_output(["rclone", "copy", tarHash + ".tar.gz", "remote:" + tarHash])
                .decode("utf-8")
                .strip()
            )
            print(res)
            subprocess.run(["mv", tarHash + ".tar.gz", home + "/TESTS/GdriveSource"])

            while True:
                try:
                    res = (
                        subprocess.check_output(
                            ["gdrive", "list", "--query", "name contains '" + tarHash + ".tar.gz" + "'", "--no-header"]
                        )
                        .decode("utf-8")
                        .strip()
                    )
                    # print(res)
                    jobKey = res.split(" ")[0]
                    print("jobKey=" + jobKey)
                except Exception as e:
                    # time.sleep(0.25)
                    print(e.output.decode("utf-8").strip())
                else:
                    break

            while True:
                try:
                    # jobKey = "1H9XSDzj15m_2IdNcblAzxk5VRWxF0CIP"
                    res = (
                        subprocess.check_output(
                            [
                                "gdrive",
                                "share",
                                jobKey,
                                "--role",
                                "writer",
                                "--type",
                                "user",
                                "--email",
                                providerToShare,
                            ]
                        )
                        .decode("utf-8")
                        .strip()
                    )
                    print(res)
                except Exception as e:
                    # time.sleep(0.25)
                    print(e.output.decode("utf-8").strip())
                else:
                    break

            if flag == 1:
                hashesFile.write(" " + str(int(lineIn[0]) - startTimeTemp) + "\n")

            flag = 1
            startTimeTemp = int(lineIn[0])
            print(f"Shared Job={idx}")
            if idx == itemsToScan - 1:
                break

            hashesFile.write(
                jobKey
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
print("\nFolders are created and shared...")

subprocess.run(["cp", path + "/hashOutput.txt", path + "/hashOutput_temp.txt"])
