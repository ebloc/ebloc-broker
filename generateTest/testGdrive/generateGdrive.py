#!/usr/bin/env python3

import os
import random
import subprocess
from os.path import expanduser

from imports import generate_md5sum
from lib import compress_folder

home = expanduser("~")
path = os.getcwd()

provider_to_share = "alper01234alper@gmail.com"
flag = 0
itemsToScan = 150 + 1
hashesFile = open(f"{path}/hashOutput.txt", "w+")
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

            random_hash = str(random.getrandbits(128)) + str(random.getrandbits(128))
            f.write("sleep " + str(int(lineIn[1]) - int(lineIn[0])) + "\n")
            f.write("#" + random_hash + "\n")  # add random line to create different hash
            f.write("echo completed " + str(int(lineIn[1]) - int(lineIn[0])) + " > completed.txt\n")
            f.close()

            folder_to_share = "ipfs"
            tar_hash = generate_md5sum(folder_to_share)
            tar_hash = tar_hash.split(" ", 1)[0]
            print("SourecodeHash=" + tar_hash)

            os.environ["fileName"] = tar_hash
            os.environ["provider_to_share"] = "alper01234alper@gmail.com"

            tar_hash, tar_path = compress_folder(folder_to_share)
            # subprocess.run(['cp', '-a', '../ipfs', '../' + tar_hash])
            print("Uploading ...")
            # rclone copy ipfs remote:ipfs
            output = (
                subprocess.check_output(["rclone", "copy", tar_hash + ".tar.gz", "remote:" + tar_hash])
                .decode("utf-8")
                .strip()
            )
            print(output)
            subprocess.run(["mv", tar_hash + ".tar.gz", home + "/TESTS/GdriveSource"])

            while True:
                try:
                    output = (
                        subprocess.check_output(
                            [
                                "gdrive",
                                "list",
                                "--query",
                                "name contains '" + tar_hash + ".tar.gz" + "'",
                                "--no-header",
                            ]
                        )
                        .decode("utf-8")
                        .strip()
                    )
                    job_key = output.split(" ")[0]
                    print("job_key=" + job_key)
                except Exception as e:
                    # time.sleep(0.25)
                    print(e.output.decode("utf-8").strip())
                else:
                    break

            while True:
                try:
                    # job_key = "1H9XSDzj15m_2IdNcblAzxk5VRWxF0CIP"
                    output = (
                        subprocess.check_output(
                            [
                                "gdrive",
                                "share",
                                job_key,
                                "--role",
                                "writer",
                                "--type",
                                "user",
                                "--email",
                                provider_to_share,
                            ]
                        )
                        .decode("utf-8")
                        .strip()
                    )
                    print(output)
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
                job_key
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
print("\nFolders are created and shared...")

subprocess.run(["cp", path + "/hashOutput.txt", path + "/hashOutput_temp.txt"])
