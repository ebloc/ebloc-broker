#!/usr/bin/env python3

import os
import subprocess
import sys
import traceback

import lib


def singleFolderShare(folderName, oc, fID) -> bool:
    try:
        # folderNames = os.listdir('/oc')
        # fID = '5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu'
        if not oc.is_shared(folderName):
            oc.share_file_with_user(folderName, fID, remote_user=True, perms=31)
            print("Sharing is completed successfully.")
            return True
        else:
            print("Requester folder is already shared.")
            return True
    except Exception:
        print(traceback.format_exc())
        return False


def eudat_initialize_folder(folderToShare, oc):
    dir_path = os.path.dirname(folderToShare)
    tar_hash = lib.compressFolder(folderToShare)
    try:
        res = oc.mkdir(tar_hash)
        print(res)
    except Exception:
        print("Folder is already created.")
        # print(traceback.format_exc())

    print("./" + tar_hash + "/" + tar_hash + ".tar.gz", tar_hash + ".tar.gz")
    try:
        status = oc.put_file("./" + tar_hash + "/" + tar_hash + ".tar.gz", dir_path + "/" + tar_hash + ".tar.gz")
        if not status:
            sys.exit()

        os.remove(dir_path + "/" + tar_hash + ".tar.gz")
    except Exception:
        print(traceback.format_exc())
        sys.exit()

    return tar_hash


def getSize(oc, f_name) -> int:
    return int(oc.file_info(f_name).attributes["{DAV:}getcontentlength"])


def isOcMounted() -> bool:
    dir_name = "/oc"
    res = None
    try:
        # cmd: findmnt --noheadings -lo source /oc
        res = subprocess.check_output(["findmnt", "--noheadings", "-lo", "source", dir_name]).decode("utf-8").strip()
    except subprocess.CalledProcessError as e:
        print("E:" + str(e))
        return False

    if not ("b2drop.eudat.eu/remote.php/webdav/" in res):
        print(
            "Mount a folder in order to access EUDAT(https://b2drop.eudat.eu/remote.php/webdav/).\n"
            "Please do: \n"
            "mkdir -p /oc \n"
            "sudo mount.davfs https://b2drop.eudat.eu/remote.php/webdav/ /oc"
        )
        return False
    else:
        return True
