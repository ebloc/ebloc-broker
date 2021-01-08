#!/usr/bin/env python3

import os
import re
import signal
import sys
import time

# from io import StringIO
from subprocess import DEVNULL, check_output

import ipfshttpclient
from cid import make_cid

from config import env, logging
from utils import _colorize_traceback, _try, compress_folder, log, run, run_with_output, silent_remove, terminate, untar


def is_valid(ipfs_hash: str) -> bool:
    try:
        make_cid(ipfs_hash)
        return True
    except:
        return False


def handler():
    """Register an handler for the timeout."""
    _colorize_traceback()
    raise Exception("E: Forever is over, end of time")


def ipfs_stat(ipfs_hash):
    """This function *may* run for an indetermined time...
    Returns a dict with the size of the block with the given hash."""
    client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001/http")
    # run(["timeout", 300, "ipfs", "object", "stat", ipfs_hash])
    return client.object.stat(ipfs_hash)


def is_hash_exists_online(ipfs_hash):
    logging.info(f"Attempting to check IPFS file {ipfs_hash}")
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(300)  # wait max 5 minutes
    try:
        output = ipfs_stat(ipfs_hash)
        print(f"CumulativeSize={output}")
        return True, output, output["CumulativeSize"]
    except KeyboardInterrupt:
        terminate("KeyboardInterrupt")
        return False, None, None
    except Exception as exc:
        logging.error(f"E: Failed to find IPFS file: {ipfs_hash}")
        print(str(exc))
        return False, None, None


def is_hash_locally_cached(ipfs_hash) -> bool:
    """Run ipfs --offline refs -r or ipfs --offline block stat etc even if your normal daemon is running.
    With that you can check if something is available locally or no."""
    try:
        check_output(["ipfs", "--offline", "block", "stat", ipfs_hash], stderr=DEVNULL)
        return True
    except Exception:
        return False


def get(ipfs_hash, path, is_storage_paid):
    output = run_with_output(["ipfs", "get", ipfs_hash, f"--output={path}"])
    logging.info(output)

    if is_storage_paid:
        # pin downloaded ipfs hash if storage is paid
        output = check_output(["ipfs", "pin", "add", ipfs_hash]).decode("utf-8").rstrip()
        logging.info(output)


def pin(ipfs_hash) -> bool:
    return run(["ipfs", "pin", "add", ipfs_hash])


def decrypt_using_gpg(gpg_file, extract_target=None):
    """This function is specific for using on driver.ipfs to decript tar file,
    specific for "tar.gz" file types.
    """
    if not os.path.isfile(f"{gpg_file}.gpg"):
        os.symlink(gpg_file, f"{gpg_file}.gpg")

    gpg_file_link = f"{gpg_file}.gpg"
    tar_file = f"{gpg_file}.tar.gz"

    """cmd:
    *    gpg --output={tar_file} --pinentry-mode loopback \
    *        --passphrase-file=f"{env.LOG_PATH}/gpg_pass.txt" \
    *        --decrypt {gpg_file_link}
    """
    cmd = [
        "gpg",
        "--batch",
        "--yes",
        f"--output={tar_file}",
        "--pinentry-mode",
        "loopback",
        f"--passphrase-file={env.LOG_PATH}/.gpg_pass.txt",
        "--decrypt",
        gpg_file_link,
    ]

    try:
        run(cmd)
        log("GPG decrypt is successfull", color="green")
        silent_remove(gpg_file)
    except:
        _colorize_traceback()
        raise
    finally:
        os.unlink(gpg_file_link)

    if not extract_target:
        try:
            untar(tar_file, extract_target)
        except:
            logging.error("E: Could not extract the given tar file")
            raise
        finally:
            cmd = None
            silent_remove(f"{extract_target}/.git")
            silent_remove(tar_file)


def gpg_encrypt(user_gpg_finderprint, target):
    is_delete = False
    if os.path.isdir(target):
        try:
            *_, encrypt_target = compress_folder(target)
            encrypted_file_target = f"{encrypt_target}.gpg"
            is_delete = True
        except:
            _colorize_traceback()
            sys.exit(1)
    else:
        if not os.path.isfile(target):
            logging.error(f"{target} does not exist")
            sys.exit(1)
        else:
            encrypt_target = target
            encrypted_file_target = f"{target}.gpg"
            is_delete = True

    if os.path.isfile(encrypted_file_target):
        log(f"==> {encrypted_file_target} is already created.")
        return encrypted_file_target

    try:
        cmd = [
            "gpg",
            "--batch",
            "--yes",
            "--recipient",
            user_gpg_finderprint,
            "--output",
            encrypted_file_target,
            "--encrypt",
            encrypt_target,
        ]
        run(cmd)
        return encrypted_file_target
    except Exception as e:
        _colorize_traceback()
        if "encryption failed: Unusable public key" in str(e.output):
            log("==> Solution: https://stackoverflow.com/a/34132924/2402577")
        raise e
    finally:
        if is_delete:
            silent_remove(encrypt_target)


def get_cumulative_size(ipfs_hash):
    return ipfs_stat(ipfs_hash)["CumulativeSize"]


def add(path: str, is_hidden=False):
    """Add file or folder into ipfs.

    :param is_hidden: boolean if it is true hidden files/foders are included such as .git
    """
    if os.path.isdir(path):
        cmd = ["ipfs", "add", "-r", "--quieter", "--progress", "--offline", path]
        if is_hidden:
            # include files that are hidden such as .git/.
            # Only takes effect on recursive add
            cmd.insert(3, "--hidden")
    elif os.path.isfile(path):
        cmd = ["ipfs", "add", "--quiet", "--progress", path]
    else:
        logging.error("E: Requested path does not exist")
        raise

    for attempt in range(10):
        try:
            result_ipfs_hash = run_with_output(cmd)
            if not result_ipfs_hash and not is_valid(result_ipfs_hash):
                logging.error(f"E: Generated new hash returned empty. Trying again. Try count: {attempt}")
                time.sleep(5)
            elif not is_valid(result_ipfs_hash):
                logging.error(f"E: Generated new hash is not valid. Trying again. Try count: {attempt}")
                time.sleep(5)
            else:
                break
        except:
            logging.error(f"E: Generated new hash returned empty. Trying again. Try count: {attempt}")
            time.sleep(5)
        else:  # success
            break
    else:  # failed all the attempts - abort
        sys.exit(1)
    return result_ipfs_hash


def get_only_ipfs_hash(path, is_hidden=True) -> str:
    """Gets only chunk and hash of a given path, do not write to disk.

    Args:
        path: Path of a folder or file

    Returns string that contains the ouput of the run commad.
    """
    if os.path.isdir(path):
        cmd = ["ipfs", "add", "-r", "--quieter", "--only-hash", path]
        if is_hidden:
            # include files that are hidden such as .git/.
            # Only takes effect on recursive add
            cmd.insert(3, "--hidden")
    elif os.path.isfile(path):
        cmd = ["ipfs", "add", "--quieter", "--only-hash", path]
    else:
        logging.error("E: Requested path does not exist")
        raise

    try:
        return _try(lambda: run(cmd))
    except Exception as e:
        raise e


def remove_lock_files():
    silent_remove(f"{env.HOME}/.ipfs/repo.lock")
    silent_remove(f"{env.HOME}/.ipfs/datastore/LOCK")


def connect_to_bootstrap_node():
    """Connects into return addresses of the currently connected peers."""
    client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001/http")
    # cmd = ["ipfs", "bootstrap", "list"]
    # output = run(cmd, is_print_trace=False)
    # s = StringIO(output)
    peers = client.bootstrap.list()["Peers"]
    peer_address = None
    for peer in peers:
        if re.search(r"/ip4/", peer) is not None:
            peer_address = peer
            break
    else:
        return False

    print(f"==> Trying to connect into {peer_address} using swarm connect")
    output = client.swarm.connect(peer_address)
    if ("connect" and "success") in str(output):
        log(str(output), "green")
        return True
    return False
