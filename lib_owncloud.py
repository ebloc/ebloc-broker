#!/usr/bin/env python3

import os
import subprocess
import sys
import time
import traceback

import owncloud

from config import logging
from lib import compress_folder, terminate


def eudat_login(user, password_path):
    # logging.innfo("Login into owncloud... ", "blue", False)
    logging.info("Login into owncloud... ")
    oc = owncloud.Client("https://b2drop.eudat.eu/")

    if user is None or user == "":
        logging.error(f"User is none")
        terminate()

    with open(password_path, "r") as content_file:
        password_path = content_file.read().strip()

    for attempt in range(5):
        try:
            oc.login(user, password_path)  # Unlocks the EUDAT account
            password_path = None
        except Exception:
            _traceback = traceback.format_exc()
            logging.error(_traceback)
            if "[Errno 110] Connection timed out" in _traceback:
                logging.warning("Sleeping for 15 seconds to overcome the max retries that exceeded.")
                time.sleep(15)
            else:
                logging.error(f"User is none")
                terminate()
        else:
            break
    else:
        logging.error(f"User is none")
        terminate()

    try:
        oc.list(".")
        logging.info("Success")
    except subprocess.CalledProcessError as e:
        logging.error(f"FAILED. {e.output.decode('utf-8').strip()}")
        terminate()

    return oc


def share_single_folder(folder_name, oc, fID) -> bool:
    try:
        # folder_names = os.listdir('/oc')
        # fID = '5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu'
        if not oc.is_shared(folder_name):
            oc.share_file_with_user(folder_name, fID, remote_user=True, perms=31)
            print("Sharing is completed successfully.")
            return True
        else:
            print("Requester folder is already shared.")
            return True
    except Exception:
        print(traceback.format_exc())
        return False


def eudat_initialize_folder(folderToShare, oc) -> bool:
    dir_path = os.path.dirname(folderToShare)
    tar_hash = compress_folder(folderToShare)
    try:
        res = oc.mkdir(tar_hash)
        print(res)
    except Exception:
        print("Folder is already created.")
        print(traceback.format_exc())

    try:
        tar_file = f"./{tar_hash}/{tar_hash}.tar.gz"
        print(tar_file)
        status = oc.put_file(tar_file, f"{dir_path}/{tar_hash}.tar.gz")
        if not status:
            return False

        os.remove(f"{dir_path}/{tar_hash}.tar.gz")
    except Exception:
        print(traceback.format_exc())
        return False

    return tar_hash


def get_size(oc, f_name) -> int:
    return int(oc.file_info(f_name).attributes["{DAV:}getcontentlength"])


def is_oc_mounted() -> bool:
    dir_name = "/oc"
    result = None
    try:
        result = subprocess.check_output(["findmnt", "--noheadings", "-lo", "source", dir_name]).decode("utf-8").strip()
    except subprocess.CalledProcessError as e:
        print(f"E: {e}")
        return False

    if not ("b2drop.eudat.eu/remote.php/webdav/" in result):
        print(
            "Mount a folder in order to access EUDAT(https://b2drop.eudat.eu/remote.php/webdav/).\n"
            "Please do: \n"
            "mkdir -p /oc \n"
            "sudo mount.davfs https://b2drop.eudat.eu/remote.php/webdav/ /oc"
        )
        return False
    else:
        return True
