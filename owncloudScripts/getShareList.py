#!/usr/bin/env python3

import os
import owncloud
from lib_owncloud import get_size

oc = owncloud.Client("https://b2drop.eudat.eu/")
oc.login("5f0db7e4-3078-4988-8fa5-f066984a8a97", "k6zik-sMQAL-TgXDA-pmWeg-7pzcz")

shareList = oc.list_open_remote_share()
# print(shareList)

for i in range(len(shareList) - 1, -1, -1):
    inputFolderName = shareList[i]["name"]
    inputFolderName = inputFolderName[1:]  # Removes '/' on the beginning
    inputID = shareList[i]["id"]
    inputOwner = shareList[i]["owner"]

    if inputFolderName == "5c3c4018fbf2e1d1ef2555ede86cf626":
        print(shareList[i])
        print(inputOwner)
        oc.accept_remote_share(int(inputID))
        print("here")

print("\n")

print(oc.list("."))


# print(oc.file_info('/3a46cc092e8681212dac00d3564f5a64.tar.gz').attributes['{DAV:}getcontentlength'])
# f_name='/17JFYbtys56cgrk2AF84qI52nAegTf9cW/17JFYbtys56cgrk2AF84qI52nAegTf9cW.tar.gz'
# print(get_size(oc, f_name))


f_name = "/5c3c4018fbf2e1d1ef2555ede86cf626/5c3c4018fbf2e1d1ef2555ede86cf626.tar.gz"
# print(oc.file_info(f_name))
print(oc.file_info(f_name).attributes)


f_name = "/5c3c4018fbf2e1d1ef2555ede86cf626"
print(oc.file_info(f_name).attributes)


# oc.get_directory_as_zip(f_name, 'alper.tar.gz')

# oc.put_file('getShareList.py', 'getShareList.py')
# print(oc.list('alper'))
# print(oc.list('9a44346985f190a0af70a6ef6f0d35ee'))
