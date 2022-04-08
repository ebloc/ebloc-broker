#!/usr/bin/env python3

import owncloud
from os.path import expanduser

from broker._utils.tools import log
from broker.config import env

f = open(expanduser("~/.ebloc-broker/.eudat_client.txt"), "r")
passw = f.read().rstrip().strip(" ")
f.close()
oc = owncloud.Client("https://b2drop.eudat.eu/")
oc.login(env.OC_USER, passw)
share_list = globals()["oc"].list_open_remote_share()
# print(share_list[0])
# print(share_list)
for i in range(len(share_list) - 1, -1, -1):
    input_folder_name = share_list[i]["name"]
    input_folder_name = input_folder_name[1:]  # removes '/' on the beginning
    input_id = share_list[i]["id"]
    input_owner = share_list[i]["owner"]
    log(dict(share_list[i]))
    print(input_owner)

    if input_folder_name == "doo":
        print(share_list[i])
        print(input_owner)

breakpoint()  # DEBUG
