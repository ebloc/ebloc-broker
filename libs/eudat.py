#!/usr/bin/env python3

import os
import os.path
import pickle
import shutil
import subprocess
import time
import traceback

import owncloud

import config
from config import env, logging
from lib import compress_folder, printc, run
from utils import _colorize_traceback, cd, popen_communicate, sleep_timer, terminate


def _upload_results(encoded_share_token, output_file_name):
    """Uploads results into Eudat using curl
    doc: https://stackoverflow.com/a/44556541/2402577, https://stackoverflow.com/a/24972004/2402577
    cmd:
    curl -X PUT -H \'Content-Type: text/plain\' -H \'Authorization: Basic \'$encoded_share_token\'==\' \
            --data-binary \'@result-\'$providerID\'-\'$index\'.tar.gz\' https://b2drop.eudat.eu/public.php/webdav/result-$providerID-$index.tar.gz

    curl --fail -X PUT -H 'Content-Type: text/plain' -H 'Authorization: Basic 'SjQzd05XM2NNcFoybk.Write'==' --data-binary
    '@0b2fe6dd7d8e080e84f1aa14ad4c9a0f_0.txt' https://b2drop.eudat.eu/public.php/webdav/result.txt
    """
    cmd = [
        "curl",
        "--fail",
        "-X",
        "PUT",
        "-H",
        "Content-Type: text/plain",
        "-H",
        f"Authorization: Basic {encoded_share_token}",
        "--data-binary",
        f"@{output_file_name}",
        f"https://b2drop.eudat.eu/public.php/webdav/{output_file_name}",
    ]
    _cmd = " ".join(cmd)
    logging.info(f"cmd: {_cmd}")  # used for test purposes

    return popen_communicate(cmd)


def upload_results(encoded_share_token, output_file_name, results_folder_prev, attempt_count=1):
    """Wrapper for the _upload_results() function"""
    with cd(results_folder_prev):
        for attempt in range(attempt_count):
            p, output, error = _upload_results(encoded_share_token, output_file_name)
            if p.returncode != 0 or "<d:error" in output:
                logging.error("E: EUDAT repository did not successfully loaded")
                logging.error(f"E: curl is failed. {p.returncode} => [{error}] {output}")
                time.sleep(1)  # wait 1 second for next step retry to upload
            else:  # success on upload
                return True
        return False


def login(user, password_path, fname: str) -> None:
    logging.info(f"Login into owncloud user:{user}")
    if os.path.isfile(fname):
        f = open(fname, "rb")
        config.oc = pickle.load(f)
        try:
            printc("Reading from the dumped object...", "blue")
            # oc.list(".")  # uncomment
            logging.info("SUCCESS. Read from dumped object.")
        except subprocess.CalledProcessError as e:
            logging.error(f"FAILED. {e.output.decode('utf-8').strip()}")

    config.oc = owncloud.Client("https://b2drop.eudat.eu/")
    if not user:
        logging.error("E: User is empty")
        terminate()

    with open(password_path, "r") as content_file:
        password = content_file.read().strip()

    for attempt in range(config.RECONNECT_ATTEMPTS):
        try:
            config.oc.login(user, password)
            password = ""
            f = open(fname, "wb")
            pickle.dump(config.oc, f)
            f.close()
        except Exception:
            _traceback = traceback.format_exc()
            _colorize_traceback()
            if "Errno 110" in _traceback or "Connection timed out" in _traceback:
                sleep_duration = 15
                logging.warning(f"Sleeping for {sleep_duration} seconds to overcome the max retries that exceeded")
                sleep_timer(sleep_duration)
            else:
                logging.error("E: Could nt connect into Eudat")
                terminate()
        else:
            break
    else:
        logging.error("E: User is None object")
        terminate()


def share_single_folder(folder_name, f_id) -> bool:
    try:
        # folder_names = os.listdir('/oc')
        # fID = '5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu'
        if not config.oc.is_shared(folder_name):
            config.oc.share_file_with_user(folder_name, f_id, remote_user=True, perms=31)
            print("Sharing is completed successfully")
            return True

        printc("=> Requester folder is already shared", "blue")
        return True
    except Exception:
        _colorize_traceback()
        return False


def initialize_folder(folder_to_share) -> str:
    dir_path = os.path.dirname(folder_to_share)
    tar_hash, tar_path = compress_folder(folder_to_share)
    tar_source = f"{dir_path}/{tar_hash}.tar.gz"
    try:
        config.oc.mkdir(tar_hash)
    except Exception as e:
        if "405" not in str(e):
            if not os.path.exists(f"{env.OWNCLOUD_PATH}/{tar_hash}"):
                try:
                    os.makedirs(f"{env.OWNCLOUD_PATH}/{tar_hash}")
                except:
                    raise
            else:
                printc("Folder is already created", "blue")
        else:
            printc("Folder is already created", "blue")

    tar_dst = f"{tar_hash}/{tar_hash}.tar.gz"

    try:
        config.oc.put_file(f"./{tar_dst}", tar_source)
        os.remove(tar_source)
    except Exception as e:
        if type(e).__name__ == "HTTPResponseError":
            try:
                shutil.copyfile(tar_source, f"{env.OWNCLOUD_PATH}/{tar_dst}")
            except:
                raise
        else:
            raise Exception("oc could not connected in order to upload the file")

    return tar_hash


def get_size(oc, f_name) -> int:
    return int(oc.file_info(f_name).attributes["{DAV:}getcontentlength"])


def is_oc_mounted() -> bool:
    mount_path = "/oc"
    output = None
    try:
        output = run(["findmnt", "--noheadings", "-lo", "source", mount_path])
    except:
        return False

    if not ("b2drop.eudat.eu/remote.php/webdav/" in output):
        print(
            "Mount a folder in order to access EUDAT(https://b2drop.eudat.eu/remote.php/webdav/).\n"
            "Please do: \n"
            "mkdir -p /oc \n"
            "sudo mount.davfs https://b2drop.eudat.eu/remote.php/webdav/ /oc"
        )
        return False
    else:
        return True
