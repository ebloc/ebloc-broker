#!/usr/bin/env python3

import os
import os.path
import pickle
import subprocess
import time
import traceback

import owncloud

from config import bp, logging  # noqa: F401
from lib import compress_folder, printc, terminate
from settings import init_env


def _upload_results(encoded_share_token, output_file_name):
    """ doc: https://stackoverflow.com/a/44556541/2402577, https://stackoverflow.com/a/24972004/2402577
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
    cmd_str = " ".join(cmd)
    logging.info(f"cmd: {cmd_str}")  # used for test purposes
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = p.communicate()
    return p, output, error


def upload_results(encoded_share_token, output_file_name, results_folder_prev, attempt_count=1):
    """Wrapper for the _upload_results() function"""
    cwd_temp = os.getcwd()
    os.chdir(results_folder_prev)
    for attempt in range(attempt_count):
        p, output, err = _upload_results(encoded_share_token, output_file_name)
        output = output.strip().decode("utf-8")
        err = err.decode("utf-8")
        if p.returncode != 0 or "<d:error" in output:
            logging.error("E: EUDAT repository did not successfully loaded.")
            print(err)
            logging.error(f"curl is failed. {p.returncode} => {err.decode('utf-8')}. {output}")
            time.sleep(1)  # wait 1 second for next step retry to upload
        else:  # success on upload
            os.chdir(cwd_temp)
            return True
    else:
        # Failed all the attempts - abort
        os.chdir(cwd_temp)
        return False


def login(user, password_path, name):
    logging.info("Login into owncloud... ")
    env = init_env()
    fname = f"{env.EBLOCPATH}/{name}"
    if os.path.isfile(fname):
        f = open(fname, "rb")
        oc = pickle.load(f)
        try:
            printc("Reading from the dumped object...", "blue")
            # oc.list(".")  # uncomment
            logging.info("SUCCESS. Read from dumped object.")
            return oc
        except subprocess.CalledProcessError as e:
            logging.error(f"FAILED. {e.output.decode('utf-8').strip()}")

    oc = owncloud.Client("https://b2drop.eudat.eu/")
    if not user:
        logging.error(f"User is empty")
        terminate()

    with open(password_path, "r") as content_file:
        password = content_file.read().strip()

    for attempt in range(5):
        try:
            # Unlocks the EUDAT account
            oc.login(user, password)
            password = None
            f = open(".oc.pckl", "wb")
            pickle.dump(oc, f)
            f.close()
            logging.info("SUCCESS")
            return oc
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
        logging.error("User is none")
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
            printc("=> Requester folder is already shared.", "blue")
            return True
    except Exception:
        print(traceback.format_exc())
        return False


def initialize_folder(folder_to_share, oc) -> str:
    dir_path = os.path.dirname(folder_to_share)
    tar_hash = compress_folder(folder_to_share)
    try:
        output = oc.mkdir(tar_hash)
        print(output)
    except Exception:
        printc("Folder is already created.", "blue")

    try:
        tar_file = f"./{tar_hash}/{tar_hash}.tar.gz"
        print(tar_file)
        success = oc.put_file(tar_file, f"{dir_path}/{tar_hash}.tar.gz")
        if not success:
            raise Exception("oc could not connected put the file")

        os.remove(f"{dir_path}/{tar_hash}.tar.gz")
    except Exception:
        print(traceback.format_exc())
        raise Exception("oc could not connected to upload the file")

    return tar_hash


def get_size(oc, f_name) -> int:
    return int(oc.file_info(f_name).attributes["{DAV:}getcontentlength"])


def is_oc_mounted() -> bool:
    mount_path = "/oc"
    output = None
    try:
        output = (
            subprocess.check_output(["findmnt", "--noheadings", "-lo", "source", mount_path]).decode("utf-8").strip()
        )
    except subprocess.CalledProcessError as e:
        print(f"E: {e}")
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
