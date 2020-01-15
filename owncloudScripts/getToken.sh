#!/usr/bin/python

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from random import randint
from os.path import expanduser
home = expanduser("~")

# Password read from the file.
f = open(home + '/.eBlocBroker/eudatPassword.txt', 'r')
password = f.read().replace("\n", "").replace(" ", "")
f.close()
oc = owncloud.Client('https://b2drop.eudat.eu/')

# 5f0db7e4-3078-4988-8fa5-f066984a8a97 == aalimog1@@boun.edu.tr
oc.login('5f0db7e4-3078-4988-8fa5-f066984a8a97', password)  # User

shareList = globals()['oc'].list_open_remote_share()
# print(shareList[0])


# print(shareList)

for i in range(len(shareList)-1, -1, -1):
    inputFolderName  = shareList[i]['name']
    inputFolderName  = inputFolderName[1:] # Removes '/' on the beginning
    inputID          = shareList[i]['id']
    inputOwner       = shareList[i]['owner']

    if inputFolderName == 'doo':
        print(shareList[i])
        print(inputOwner)
