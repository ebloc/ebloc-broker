#!/usr/bin/env python3

import hashlib
import os
import os.path
import owncloud
import pickle
import shutil
import subprocess
import sys
import time
from contextlib import suppress
from pathlib import Path
from web3.logs import DISCARD

from broker import cfg, config
from broker._utils._log import br, ok
from broker._utils.web3_tools import get_tx_status
from broker.config import env, logging
from broker.errors import QuietExit
from broker.lib import calculate_size, run
from broker.libs import _git
from broker.utils import cd, compress_folder, log, popen_communicate, print_tb, sleep_timer, terminate

Ebb = cfg.Ebb


def _upload_results(encoded_share_token, output_file_name):
    r"""Upload results into Eudat using curl.

    * How to upload files into shared b2drop.eudat(owncloud) repository using curl?
    __ https://stackoverflow.com/a/44556541/2402577

    * commands(s):
    curl -X PUT -H \'Content-Type: text/plain\' -H \'Authorization: Basic \'$encoded_share_token\'==\' \
        --data-binary \'@result-\'$providerID\'-\'$index\'.tar.gz\' \
        https://b2drop.eudat.eu/public.php/webdav/result-$providerID-$index.tar.gz

    curl --fail -X PUT -H 'Content-Type: text/plain' -H 'Authorization: Basic \
        'SjQzd05XM2NNcFoybk.Write'==' --data-binary '@0b2fe6dd7d8e080e84f1aa14ad4c9a0f_0.txt' \
        https://b2drop.eudat.eu/public.php/webdav/result.txt
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
    cmd_temp[5] = f'"{cmd[5]}" \   \n    '
    cmd_temp[7] = f'"{cmd[7]}" \   \n    '
    cmd_temp[9] = f'"{cmd[9]}" \   \n    '
    cmd_temp[10] = f'"{cmd[10]}" \ \n    '
    cmd_str = " ".join(cmd_temp)
    log(f"==> cmd:\n{cmd_str}")
    return popen_communicate(cmd)


def upload_results(encoded_share_token, output_file_name, path, max_retries=1):
    """Implement wrapper for the _upload_results function."""
    with cd(path):
        for _ in range(max_retries):
            p, output, error = _upload_results(encoded_share_token, output_file_name)
            if error:
                log(error)

            if "warning: Couldn't read data from file" in error:
                raise Exception("Eudat repository did not successfully uploaded")

            if p.returncode != 0 or "<d:error" in output:
                log("Eudat repository did not successfully uploaded")
                log(f"   curl is failed. {p.returncode} => {br(error)} {output}")
                time.sleep(1)  # wait 1 second for next step retry to upload
            else:  # success on upload
                return True

        raise Exception(f"Upload results into cloud failed after {max_retries} tries")


def _login(fn, user, password_path) -> None:
    sleep_duration = 15
    config.oc = owncloud.Client("https://b2drop.eudat.eu/")
    with open(password_path, "r") as content_file:
        password = content_file.read().strip()

    for _ in range(config.RECONNECT_ATTEMPTS):
        try:
            status_str = f"Trying to login into owncloud user=[yellow]{user}[/yellow] ..."
            with cfg.console.status(status_str):
                # may take few minutes to connect
                config.oc.login(user, password)

            password = ""
            f = open(fn, "wb")
            pickle.dump(config.oc, f)
            f.close()
            log(f"  {status_str} {ok()}")
            return
        except Exception as e:
            log(str(e))
            if "Errno 110" in str(e) or "Connection timed out" in str(e):
                log(f"warning: sleeping for {sleep_duration} seconds to overcome the max retries that exceeded")
                sleep_timer(sleep_duration)
            else:
                terminate("Could not connect into [blue]eudat using config.oc.login()[/blue]")

    logging.error("E: user is None object")
    terminate()


def login(user, password_path: Path, fn: str) -> None:
    if not user:
        log("E: Given user is empty string")
        terminate()

    if os.path.isfile(fn):
        f = open(fn, "rb")
        config.oc = pickle.load(f)
        try:
            status_str = (
                f"[bold]Login into owncloud from the dumped_object=[magenta]{fn}[/magenta] [yellow]...[/yellow]"
            )
            with cfg.console.status(status_str):
                config.oc.get_config()

            log(f" {status_str} {ok()}")
        except subprocess.CalledProcessError as e:
            logging.error(f"FAILED. {e.output.decode('utf-8').strip()}")
            _login(fn, user, password_path)
    else:
        _login(fn, user, password_path)


def share_single_folder(folder_name, f_id) -> bool:
    try:
        # folder_names = os.listdir(env.OWNCLOUD_PATH)
        # fID = '5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu'
        if not config.oc.is_shared(folder_name):
            config.oc.share_file_with_user(folder_name, f_id, remote_user=True, perms=31)
            log(f"sharing with [yellow]{f_id}[/yellow]{ok()}", "bold")
            return True

        log("## Requester folder is already shared")
        return True
    except Exception as e:
        print_tb(e)
        return False


def initialize_folder(folder_to_share, requester_name) -> str:
    dir_path = os.path.dirname(folder_to_share)
    tar_hash, *_ = compress_folder(folder_to_share)
    tar_source = f"{dir_path}/{tar_hash}.tar.gz"
    try:
        config.oc.mkdir(f"{tar_hash}_{requester_name}")
    except Exception as e:
        if "405" not in str(e):
            if not os.path.exists(f"{env.OWNCLOUD_PATH}/{tar_hash}_{requester_name}"):
                try:
                    os.makedirs(f"{env.OWNCLOUD_PATH}/{tar_hash}_{requester_name}")
                except Exception as e:
                    raise e
            else:
                log("#> folder is already created")
        else:
            log("#> folder is already created")

    try:
        tar_dst = f"{tar_hash}_{requester_name}/{tar_hash}.tar.gz"
        log("## uploading into [green]EUDAT B2DROP[/green] this may take some time depending on the file size...")
        is_already_uploaded = False
        with suppress(Exception):
            # File is first time created
            size = calculate_size(tar_source, _type="bytes")
            file_info = config.oc.file_info(f"./{tar_dst}")
            log(file_info, "bold")
            if float(file_info.attributes["{DAV:}getcontentlength"]) == size:
                # check is it already uploaded or not via its file size
                log(f"## {tar_source} is already uploaded into [green]EUDAT B2DROP")
                is_already_uploaded = True

        if not is_already_uploaded:
            config.oc.put_file(f"./{tar_dst}", tar_source)

        os.remove(tar_source)
    except Exception as e:
        if type(e).__name__ == "HTTPResponseError":
            try:
                shutil.copyfile(tar_source, f"{env.OWNCLOUD_PATH}/{tar_dst}")
            except Exception as e:
                raise e
        else:
            raise Exception("oc could not connected in order to upload the file")  # noqa

    return tar_hash


def get_size(f_name, oc=None) -> int:
    if oc is None:
        oc = config.oc

    return int(oc.file_info(f_name).attributes["{DAV:}getcontentlength"])


def is_oc_mounted() -> bool:
    output = None
    try:
        output = run(["findmnt", "--noheadings", "-lo", "source", env.OWNCLOUD_PATH])
    except:
        return False

    if "b2drop.eudat.eu/remote.php/webdav/" not in output:
        print(
            "Mount a folder in order to access EUDAT(https://b2drop.eudat.eu/remote.php/webdav/).\n"
            "Please do: \n"
            "sudo mkdir -p /oc \n"
            "sudo mount.davfs https://b2drop.eudat.eu/remote.php/webdav/ /oc"
        )
        return False
    else:
        return True


def submit(provider, requester, job, required_confs=1):
    try:
        tx_hash = _submit(provider, requester, job, required_confs)
        if required_confs >= 1:
            tx_receipt = get_tx_status(tx_hash)
            if tx_receipt["status"] == 1:
                processed_logs = Ebb._eblocbroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
                log(vars(processed_logs[0].args))
                try:
                    log(f"{ok()} [bold]job_index={processed_logs[0].args['index']}")
                except IndexError:
                    log(f"E: Tx({tx_hash}) is reverted")
        else:
            log(f"tx_hash={tx_hash}", "bold")
    except QuietExit:
        pass
    except Exception as e:
        print_tb(e)

    return tx_hash


def _submit(provider, requester, job, required_confs=1):
    job.Ebb.is_requester_valid(requester)
    job.Ebb.is_eth_account_locked(requester)
    provider = cfg.w3.toChecksumAddress(provider)
    provider_info = job.Ebb.get_provider_info(provider)
    requester_name = hashlib.md5(requester.lower().encode("utf-8")).hexdigest()[:16]
    log(f"==> provider_fid=[magenta]{provider_info['f_id']}")
    try:
        _git.is_repo(job.folders_to_share)
    except:
        print_tb()
        sys.exit(1)

    for idx, folder in enumerate(job.folders_to_share):
        if not isinstance(folder, bytes):
            if idx != 0:
                print("")

            log(f"==> folder_to_share={folder}")
            try:
                _git.initialize_check(folder)
                _git.commit_changes(folder)
                folder_hash = initialize_folder(folder, requester_name)
            except Exception as e:
                print_tb(e)
                sys.exit(1)

            if idx == 0:
                job_key = folder_hash

            # required to send string as bytes
            value = cfg.w3.toBytes(text=folder_hash)
            job.code_hashes.append(value)
            job.code_hashes_str.append(value.decode("utf-8"))
            if not share_single_folder(f"{folder_hash}_{requester_name}", provider_info["f_id"]):
                sys.exit(1)

            time.sleep(0.25)
        else:
            code_hash = folder
            job.code_hashes.append(code_hash)
            job.code_hashes_str.append(code_hash.decode("utf-8"))

    job.price, *_ = job.cost(provider, requester)
    # print(job.code_hashes)
    try:
        return job.Ebb.submit_job(provider, job_key, job, requester, required_confs=required_confs)
    except QuietExit:
        sys.exit(1)
    except Exception as e:
        print_tb(e)
        # log(f"E: Unlock your Ethereum Account({requester})")
        # log("#> In order to unlock an account you can use: ~/eBlocPOA/client.sh")
        sys.exit(1)
