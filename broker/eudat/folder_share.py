#!/usr/bin/python

import os
from os.path import expanduser

from broker import config
from broker.config import env
from broker.libs import eudat


def main():
    user = "aalimog1@@boun.edu.tr"
    passwd = expanduser("~/.ebloc-broker/.eudat_client.txt")
    eudat.login(user, passwd, env.OC_CLIENT)
    folder_names = os.listdir(expanduser("/mnt/oc"))
    for idx in range(0, len(folder_names) - 1):
        name = folder_names[idx]
        if not config.oc.is_shared(name):
            config.oc.share_file_with_user(
                name,
                "dc0f981c-bed2-432a-9064-844e2d182c5a@b2drop.eudat.eu",
                remote_user=True,
                perms=31,
            )


if __name__ == "__main__":
    main()
