#!/usr/bin/python

import os
from os.path import expanduser

from broker import config
from broker.config import env
from broker.libs import eudat

eudat.login("aalimog1@@boun.edu.tr", expanduser("~/.ebloc-broker/password_owncloud.txt"), env.OC_CLIENT)
folder_names = os.listdir(expanduser("~/oc"))
for i in range(0, len(folder_names) - 1):
    name = folder_names[i]
    if not config.oc.is_shared(name):
        config.oc.share_file_with_user(
            name,
            "dc0f981c-bed2-432a-9064-844e2d182c5a@b2drop.eudat.eu",
            remote_user=True,
            perms=31,
        )
