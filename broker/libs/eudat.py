#!/usr/bin/env python3

import os
import os.path
import pickle
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path
from pprint import pprint

import owncloud
from web3.logs import DISCARD

import broker.cfg as cfg
import broker.config as config
import broker.libs.git as git
from broker._utils._log import br, ok
from broker._utils.tools import QuietExit
from broker.config import env, logging
from broker.eblocbroker.job import Job
from broker.lib import get_tx_status, run
from broker.utils import (
    CacheType,
    StorageID,
    cd,
    compress_folder,
    log,
    popen_communicate,
    print_tb,
    sleep_timer,
    terminate,
)

Ebb = cfg.Ebb


def _upload_results(encoded_share_token, output_file_name):
    """Upload results into Eudat using curl.

    - (How to upload files into shared b2drop.eudat(owncloud) repository using
      curl?)[https://stackoverflow.com/a/44556541/2402577]

    __ https://stackoverflow.com/a/24972004/2402577

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
        "-w",
        "%{http_code}\n"
        # "-v"  # verbose
    ]

    # some arguments requires "" for curl to work
    cmd_temp = cmd.copy()
    cmd_temp[5] = f'"{cmd[5]}" \ \n    '
    cmd_temp[7] = f'"{cmd[7]}" \ \n    '
    cmd_temp[9] = f'"{cmd[9]}" \ \n    '
    cmd_str = " ".join(cmd_temp)
    log(f"==> cmd:\n{cmd_str}\n")  # used for test purposes
    return popen_communicate(cmd)


def upload_results(encoded_share_token, output_file_name, path, max_retries=1):
    """Implement wrapper for the _upload_results() function."""
    with cd(path):
        for _ in range(max_retries):
            p, output, error = _upload_results(encoded_share_token, output_file_name)
            if error:
                log(error)

            if "Warning: Couldn't read data from file" in error:
                logging.error("E: EUDAT repository did not successfully uploaded")
                return False

            if p.returncode != 0 or "<d:error" in output:
                logging.error("E: EUDAT repository did not successfully uploaded")
                logging.error(f"E: curl is failed. {p.returncode} => {br(error)} {output}")
                time.sleep(1)  # wait 1 second for next step retry to upload
            else:  # success on upload
                return True
        return False


def _login(fname, user, password_path):
    sleep_duration = 15
    config.oc = owncloud.Client("https://b2drop.eudat.eu/")
    with open(password_path, "r") as content_file:
        password = content_file.read().strip()

    for _ in range(config.RECONNECT_ATTEMPTS):
        try:
            log("==> Trying to login into owncloud ", end="")
            config.oc.login(user, password)  # May take long time to connect
            password = ""
            f = open(fname, "wb")
            pickle.dump(config.oc, f)
            f.close()
            log(ok())
        except Exception as e:
            print_tb(e)
            _traceback = traceback.format_exc()
            if "Errno 110" in _traceback or "Connection timed out" in _traceback:
                logging.warning(f"Sleeping for {sleep_duration} seconds to overcome the max retries that exceeded")
                sleep_timer(sleep_duration)
            else:
                logging.error("E: Could not connect into Eudat")
                terminate()
        else:
            return False
    logging.error("E: User is None object")
    terminate()


def login(user, password_path: Path, fname: str) -> None:
    if not user:
        logging.error("E: User is empty")
        terminate()

    if os.path.isfile(fname):
        f = open(fname, "rb")
        config.oc = pickle.load(f)
        try:
            log(f"## Login into owncloud from the dumped object={fname} ", end="")
            config.oc.get_config()
            log(ok())
        except subprocess.CalledProcessError as e:
            logging.error(f"FAILED. {e.output.decode('utf-8').strip()}")
            _login(fname, user, password_path)
    else:
        _login(fname, user, password_path)


def share_single_folder(folder_name, f_id) -> bool:
    try:
        # folder_names = os.listdir('/oc')
        # fID = '5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu'
        if not config.oc.is_shared(folder_name):
            config.oc.share_file_with_user(folder_name, f_id, remote_user=True, perms=31)
            log(f"{ok()} Sharing")
            return True

        log("## Requester folder is already shared")
        return True
    except Exception as e:
        print_tb(e)
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
                except Exception as e:
                    raise e
            else:
                log("==> Folder is already created")
        else:
            log("==> Folder is already created")

    tar_dst = f"{tar_hash}/{tar_hash}.tar.gz"

    try:
        config.oc.put_file(f"./{tar_dst}", tar_source)
        os.remove(tar_source)
    except Exception as e:
        if type(e).__name__ == "HTTPResponseError":
            try:
                shutil.copyfile(tar_source, f"{env.OWNCLOUD_PATH}/{tar_dst}")
            except Exception as e:
                raise e
        else:
            raise Exception("oc could not connected in order to upload the file")

    return tar_hash


def get_size(f_name, oc=None) -> int:
    if oc is None:
        oc = config.oc
    return int(oc.file_info(f_name).attributes["{DAV:}getcontentlength"])


def is_oc_mounted() -> bool:
    mount_path = "/oc"
    output = None
    try:
        output = run(["findmnt", "--noheadings", "-lo", "source", mount_path])
    except:
        return False

    if "b2drop.eudat.eu/remote.php/webdav/" not in output:
        print(
            "Mount a folder in order to access EUDAT(https://b2drop.eudat.eu/remote.php/webdav/).\n"
            "Please do: \n"
            "mkdir -p /oc \n"
            "sudo mount.davfs https://b2drop.eudat.eu/remote.php/webdav/ /oc"
        )
        return False
    else:
        return True


def submit(provider, requester, folders_to_share):
    try:
        tx_hash = _submit(provider, requester, folders_to_share)
        tx_receipt = get_tx_status(tx_hash)
        if tx_receipt["status"] == 1:
            processed_logs = Ebb._eBlocBroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
            pprint(vars(processed_logs[0].args))
            try:
                log(f"{ok()} [bold]job_index={processed_logs[0].args['index']}")
            except IndexError:
                log(f"E: Tx({tx_hash}) is reverted")
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)


def _submit(provider, requester, folders_to_share):
    job = Job()
    job.Ebb.is_requester_valid(requester)
    job.Ebb.is_eth_account_locked(requester)
    provider = cfg.w3.toChecksumAddress(provider)
    provider_info = job.Ebb.get_provider_info(provider)
    log(f"==> provider.f_id={provider_info['f_id']}")
    job.folders_to_share = folders_to_share.copy()
    try:
        git.is_repo(job.folders_to_share)
    except:
        print_tb()
        sys.exit(1)

    log()
    for idx, folder in enumerate(job.folders_to_share):
        if idx != 0:
            print("")

        log(f"==> folder_to_share={folder}")
        try:
            git.initialize_check(folder)
            git.commit_changes(folder)
            folder_hash = initialize_folder(folder)
        except:
            print_tb()
            sys.exit(1)

        if idx == 0:
            job_key = folder_hash

        # required to send string as bytes
        value = cfg.w3.toBytes(text=folder_hash)
        job.source_code_hashes.append(value)
        job.source_code_hashes_str.append(value.decode("utf-8"))
        if not share_single_folder(folder_hash, provider_info["f_id"]):
            sys.exit(1)

        time.sleep(0.25)

    log()
    log("==> Submitting the job")
    job.run_time = [60]  # in seconds
    job.cores = [1]
    job.data_transfer_ins = [1, 100]
    job.data_transfer_out = 1
    job.storage_ids = [StorageID.EUDAT, StorageID.EUDAT]
    job.cache_types = [CacheType.PRIVATE, CacheType.PUBLIC]
    job.storage_hours = [1, 1]
    job.data_prices_set_block_numbers = [0, 0]
    print(job.source_code_hashes)
    job_price, cost = job.cost(provider, requester)
    try:
        return job.Ebb.submit_job(provider, job_key, job_price, job, requester)
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)
        log(f"E: Unlock your Ethereum Account({requester})")
        log("In order to unlock an account you can use: ~/eBlocPOA/client.sh", "yellow")
        sys.exit(1)
