#!/usr/bin/python

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from random import randint

path = os.getcwd();

f = open("/home/prc/multiple/eudat/password.txt", 'r'); # Password read from the file.
password = f.read().replace("\n", "").replace(" ", "");
f.close();

oc = owncloud.Client('https://b2drop.eudat.eu/');
oc.login('alper.alimoglu@boun.edu.tr', password);

folderNames=os.listdir("oc");

for i in range(0, len(folderNames)-1): #{
    name = folderNames[i];
    print(name);
    if not oc.is_shared(name):
        oc.share_file_with_user(name, 'ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu', remote_user=True, perms=31);
#}
