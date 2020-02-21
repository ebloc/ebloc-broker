#!/usr/bin/python

import os
from os.path import expanduser

from lib_owncloud import eudat_login

home = expanduser("~")

oc = eudat_login("aalimog1@@boun.edu.tr", "/home/alper/.eBlocBroker/password_owncloud.txt")
folderNames = os.listdir(home + "/oc")

for i in range(0, len(folderNames) - 1):
    name = folderNames[i]
    if not oc.is_shared(name):
        oc.share_file_with_user(
            name, "dc0f981c-bed2-432a-9064-844e2d182c5a@b2drop.eudat.eu", remote_user=True, perms=31
        )
