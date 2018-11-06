#!/usr/bin/python

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from random import randint
from os.path import expanduser
home = expanduser("~")

# Password read from the file.
f = open('/home/alper/.eBlocBroker/password_owncloud.txt', 'r') 
password = f.read().replace("\n", "").replace(" ", "")
f.close()
oc = owncloud.Client('https://b2drop.eudat.eu/')
oc.login('aalimog1@@boun.edu.tr', password) # User

folderNames = os.listdir(home + "/oc")
   
for i in range(0, len(folderNames)-1): #{
    name = folderNames[i]
    if not oc.is_shared(name):
        oc.share_file_with_user(name, 'dc0f981c-bed2-432a-9064-844e2d182c5a@b2drop.eudat.eu', remote_user=True, perms=31)
#}
