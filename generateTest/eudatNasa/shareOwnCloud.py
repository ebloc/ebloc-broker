#!/usr/bin/python

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from os.path import expanduser
from random import randint

path = os.getcwd();
home = expanduser("~")

# Login to EUDAT account----------------------------------------
f = open(home + "/TESTS/password.txt", 'r')  # Password read from the file.
password = f.read().replace("\n", "").replace(" ", "")
f.close()
oc = owncloud.Client('https://b2drop.eudat.eu/')
oc.login('059ab6ba-4030-48bb-b81b-12115f531296', password)
#---------------------------------------------------------------
folderNames=os.listdir(home + "/oc");
for i in range(0, len(folderNames)-1):
    name = folderNames[i];
    print(name);
    if not oc.is_shared(name):
        oc.share_file_with_user(name, '5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu', remote_user=True, perms=31);
