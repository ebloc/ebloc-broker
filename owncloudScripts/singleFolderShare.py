#!/usr/bin/python

import owncloud, hashlib, getpass, os, time, math, datetime, random, sys
from random import randint
from os.path import expanduser
home = expanduser("~")

def singleFolderShare(folderName, oc=None): 
    # folderNames = os.listdir(home + "/oc")    
    if oc is None:
        # Password read from the file.
        f = open( '/home/alper/.eBlocBroker/password_owncloud.txt', 'r') 
        password = f.read().replace("\n", "").replace(" ", "")
        f.close()
        oc = owncloud.Client('https://b2drop.eudat.eu/')
        oc.login('059ab6ba-4030-48bb-b81b-12115f531296', password)
        password = None
    print(folderName)
    if not oc.is_shared(folderName):
        oc.share_file_with_user(folderName, '5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu', remote_user=True, perms=31)
        return 'Sharing is completed successfully.'
    else:
        return 'Already shared.'

if __name__ == '__main__': 
    if len(sys.argv) is not 2:
        print('Please provide folder name.')
        sys.exit()
    folderName = sys.argv[1]

    res = singleFolderShare(folderName)
    print(res)
