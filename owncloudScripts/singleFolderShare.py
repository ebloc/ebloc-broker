#!/usr/bin/python

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from random import randint

if len(sys.argv) is not 2:
    print('Please provide folder name.')
    sys.exit()

folderName = sys.argv[1]

# Password read from the file.
f = open( 'password.txt', 'r') 
password = f.read().replace("\n", "").replace(" ", "")
f.close()
oc = owncloud.Client('https://b2drop.eudat.eu/')
oc.login('alper.alimoglu@boun.edu.tr', password)

folderNames = os.listdir("oc")

if not oc.is_shared(folderName):
    oc.share_file_with_user(folderName, 'ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu', remote_user=True, perms=31)
    print('Shared')
else:
    print('Already shared')          
          
