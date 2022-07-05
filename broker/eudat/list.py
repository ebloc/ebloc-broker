#!/usr/bin/env python3

import owncloud

from broker.config import env
from broker.utils import print_tb


def share_list(oc):
    share_list = oc.list_open_remote_share()
    for i in range(len(share_list) - 1, -1, -1):
        input_folder_name = share_list[i]["name"]
        input_folder_name = input_folder_name[1:]  # removes '/' on the beginning
        owner = share_list[i]["owner"]
        if input_folder_name == "5c3c4018fbf2e1d1ef2555ede86cf626":
            print(share_list[i])
            print(owner)
            oc.accept_remote_share(int(share_list[i]["id"]))
            print("here")

    # print(oc.file_info('/3a46cc092e8681212dac00d3564f5a64.tar.gz').attributes['{DAV:}getcontentlength'])
    # fn = '/17JFYbtys56cgrk2AF84qI52nAegTf9cW/17JFYbtys56cgrk2AF84qI52nAegTf9cW.tar.gz'
    # print(eudat.get_size(fn, oc))
    fn = "/5c3c4018fbf2e1d1ef2555ede86cf626/5c3c4018fbf2e1d1ef2555ede86cf626.tar.gz"
    # print(oc.file_info(fn))
    print(oc.file_info(fn).attributes)
    fn = "/5c3c4018fbf2e1d1ef2555ede86cf626"
    print(oc.file_info(fn).attributes)
    # oc.get_directory_as_zip(fn, 'dummy.tar.gz')
    # oc.put_file('getShareList.py', 'getShareList.py')
    # print(oc.list('dummy_dir'))
    # print(oc.list('9a44346985f190a0af70a6ef6f0d35ee'))


def main():
    oc = owncloud.Client("https://b2drop.eudat.eu/")
    with open(env.LOG_PATH.joinpath(".eudat_client.txt"), "r") as content_file:
        paswd = content_file.read().strip()

    try:
        oc.login(env.OC_USER, paswd)
        print(oc.list("."))
        oc.mkdir("dummy_dir")
    except Exception as e:
        print_tb(e)

    # share_list(oc)


if __name__ == "__main__":
    main()
