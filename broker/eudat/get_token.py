#!/usr/bin/python

from os.path import expanduser

import owncloud

f = open(expanduser("~/.ebloc-broker/eudat_password.txt"), "r")
password = f.read().rstrip().strip(" ")
f.close()

oc = owncloud.Client("https://b2drop.eudat.eu/")

# 5f0db7e4-3078-4988-8fa5-f066984a8a97 == aalimog1@@boun.edu.tr
oc.login("5f0db7e4-3078-4988-8fa5-f066984a8a97", password)  # user
share_list = globals()["oc"].list_open_remote_share()
# print(share_list[0])
# print(share_list)

for i in range(len(share_list) - 1, -1, -1):
    input_folder_name = share_list[i]["name"]
    input_folder_name = input_folder_name[1:]  # removes '/' on the beginning
    input_id = share_list[i]["id"]
    input_owner = share_list[i]["owner"]
    if input_folder_name == "doo":
        print(share_list[i])
        print(input_owner)
