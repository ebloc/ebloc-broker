#!/usr/bin/python

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from random import randint
from os.path import expanduser
home = expanduser("~")

if len(sys.argv) is not 2:
    print('Please provide folder name.')
    sys.exit()

folderName = sys.argv[1]

# Password read from the file.
f = open( 'password.txt', 'r') 
password = f.read().replace("\n", "").replace(" ", "")
f.close()
oc = owncloud.Client('https://b2drop.eudat.eu/')
oc.login('059ab6ba-4030-48bb-b81b-12115f531296', password)

print(folderName)
if not oc.is_shared(folderName):
    oc.share_file_with_user(folderName, '5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu', remote_user=True, perms=31)
    print('Sharing is completed successfully.')
else:
    print('Already shared.')

# folderNames = os.listdir(home + "/oc")
