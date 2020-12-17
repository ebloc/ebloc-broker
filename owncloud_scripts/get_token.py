#!/usr/bin/python

from os.path import expanduser

import owncloud

home = expanduser("~")

# password read from the file
f = open(home + "/.eBlocBroker/eudat_password.txt", "r")
password = f.read().rstrip().strip(" ")
f.close()

oc = owncloud.Client("https://b2drop.eudat.eu/")

# 5f0db7e4-3078-4988-8fa5-f066984a8a97 == aalimog1@@boun.edu.tr
oc.login("5f0db7e4-3078-4988-8fa5-f066984a8a97", password)  # user

shareList = globals()["oc"].list_open_remote_share()
# print(shareList[0])
# print(shareList)

for i in range(len(shareList) - 1, -1, -1):
    inputFolderName = shareList[i]["name"]
    inputFolderName = inputFolderName[1:]  # removes '/' on the beginning
    inputID = shareList[i]["id"]
    inputOwner = shareList[i]["owner"]

    if inputFolderName == "doo":
        print(shareList[i])
        print(inputOwner)
