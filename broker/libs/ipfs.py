#!/usr/bin/env python3

import json
import os
import re
import signal
import sys
import time
from subprocess import DEVNULL, check_output

import ipfshttpclient
from cid import make_cid

from broker._utils._log import ok
from broker._utils.tools import handler, log, print_tb
from broker.utils import question_yes_no

# from io import StringIO
from broker.config import env, logging
from broker.utils import (
    _remove,
    _try,
    compress_folder,
    is_ipfs_on,
    popen_communicate,
    raise_error,
    run,
    run_with_output,
    terminate,
    untar,
)


class IpfsNotConnected(Exception):
    pass


class Ipfs:
    def __init__(self):
        """Initialize ipfshttpclient object."""
        self.connect()

    def connect(self):
        """Connect into ipfs."""
        if is_ipfs_on(is_print=False):
            self.client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001/http")

    #################
    # OFFLINE CALLS #
    #################
    def is_valid(self, ipfs_hash: str) -> bool:
        try:
            make_cid(ipfs_hash)
            return True
        except:
            return False

    def is_hash_locally_cached(self, ipfs_hash: str) -> bool:
        """Return true if hash locally cached.

        Run `ipfs --offline refs -r` or `ipfs --offline block stat` etc even if your normal daemon is running.
        With that you can check if something is available locally or no.
        """
        try:
            check_output(["ipfs", "--offline", "block", "stat", ipfs_hash], stderr=DEVNULL)
            return True
        except Exception as e:
            log(f"E: {e}")
            return False

    def pin(self, ipfs_hash: str) -> bool:
        return run(["ipfs", "pin", "add", ipfs_hash])

    def decrypt_using_gpg(self, gpg_file, extract_target=None):
        """Decrypt compresses file using gpg.

        This function is specific for using on driver.ipfs to decript tar file,
        specific for "tar.gz" file types.

        cmd:
        gpg --verbose --output={tar_file} --pinentry-mode loopback \
            --passphrase-file=f"{env.LOG_PATH}/gpg_pass.txt" \
            --decrypt {gpg_file_link}
        """
        if not os.path.isfile(f"{gpg_file}.gpg"):
            os.symlink(gpg_file, f"{gpg_file}.gpg")

        gpg_file_link = f"{gpg_file}.gpg"
        tar_file = f"{gpg_file}.tar.gz"
        cmd = [
            "gpg",
            "--verbose",
            "--batch",
            "--yes",
            f"--output={tar_file}",
            "--pinentry-mode",
            "loopback",
            f"--passphrase-file={env.GPG_PASS_FILE}",
            "--decrypt",
            gpg_file_link,
        ]
        try:
            run(cmd)
            log(f"==> GPG decrypt {ok()}")
            _remove(gpg_file)
            os.unlink(gpg_file_link)
        except Exception as e:
            print_tb(e)
            raise e
            # breakpoint()  # DEBUG
        # finally:
        #     os.unlink(gpg_file_link)
        if extract_target:
            try:
                untar(tar_file, extract_target)
            except:
                raise Exception("E: Could not extract the given tar file")
            finally:
                cmd = None
                _remove(f"{extract_target}/.git")
                _remove(tar_file)

    def remove_lock_files(self):
        _remove(f"{env.HOME}/.ipfs/repo.lock", is_warning=True)
        _remove(f"{env.HOME}/.ipfs/datastore/LOCK", is_warning=True)

    def gpg_encrypt(self, user_gpg_finderprint, target):
        is_delete = False
        if os.path.isdir(target):
            try:
                *_, encrypt_target = compress_folder(target)
                encrypted_file_target = f"{encrypt_target}.gpg"
                is_delete = True
            except Exception as e:
                print_tb(e)
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
            log(f"## gpg_file: {encrypted_file_target} is already created")
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
            log(f"==> gpg_file={encrypted_file_target}")
            return encrypted_file_target
        except Exception as e:
            print_tb(e)
            if "encryption failed: Unusable public key" in str(e):
                log("==> Check solution: https://stackoverflow.com/a/34132924/2402577")
        finally:
            if is_delete:
                _remove(encrypt_target)

    ################
    # ONLINE CALLS #
    ################
    def swarm_connect(self, ipfs_id: str):
        """Swarm connect into the ipfs node."""
        if not is_ipfs_on():
            raise IpfsNotConnected

        # TODO: check is valid IPFS id
        try:
            log(f" * trying to connect into {ipfs_id} ", end="")
            # output = client.swarm.connect(provider_info["ipfs_id"])
            # if ("connect" and "success") in str(output):
            #     log(str(output), "green")
            cmd = ["ipfs", "swarm", "connect", ipfs_id]
            p, output, error = popen_communicate(cmd)
            if p.returncode != 0:
                log()
                if "failure: dial to self attempted" in error:
                    log(f"Warning: {error.replace('Error: ', '').rstrip()}")
                    question_yes_no("#> Would you like to continue?")
                else:
                    raise Exception(error)
            else:
                log(ok())
        except Exception as e:
            print_tb(e)
            log("E: connection into provider's IPFS node via swarm is not accomplished")
            sys.exit(1)

    def _ipfs_stat(self, ipfs_hash):
        """Return stats of the give IPFS hash.

        This function *may* run for an indetermined time. Returns a dict with the
        size of the block with the given hash.
        """
        if not is_ipfs_on():
            raise IpfsNotConnected

        # run(["timeout", 300, "ipfs", "object", "stat", ipfs_hash])
        return self.client.object.stat(ipfs_hash)

    def is_hash_exists_online(self, ipfs_hash: str):
        logging.info(f"Attempting to check IPFS file {ipfs_hash}")
        if not is_ipfs_on():
            raise IpfsNotConnected

        # Set the signal handler and a 300-second alarm
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(300)
        try:
            output = self._ipfs_stat(ipfs_hash)
            output_json = json.dumps(output.as_json(), indent=4, sort_keys=True)
            log(f"CumulativeSize {output_json}", "bold green")
            return output, output["CumulativeSize"]
        except KeyboardInterrupt:
            terminate("KeyboardInterrupt")
        except Exception as e:
            raise Exception(f"E: Failed to find IPFS file: {ipfs_hash}. {e}")

    def get(self, ipfs_hash, path, is_storage_paid):
        if not is_ipfs_on():
            raise IpfsNotConnected

        output = run_with_output(["ipfs", "get", ipfs_hash, f"--output={path}"])
        logging.info(output)
        if is_storage_paid:
            # pin downloaded ipfs hash if storage is paid
            output = check_output(["ipfs", "pin", "add", ipfs_hash]).decode("utf-8").rstrip()
            logging.info(output)

    def get_cumulative_size(self, ipfs_hash: str):
        if not is_ipfs_on():
            raise IpfsNotConnected

        return self._ipfs_stat(ipfs_hash)["CumulativeSize"]

    def add(self, path: str, is_hidden=False) -> str:
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
            raise_error(f"E: Requested path {path} does not exist")

        for attempt in range(10):
            try:
                result_ipfs_hash = run_with_output(cmd)
                if not result_ipfs_hash and not self.is_valid(result_ipfs_hash):
                    logging.error(f"E: Generated new hash returned empty. Trying again. Try count: {attempt}")
                    time.sleep(5)
                elif not self.is_valid(result_ipfs_hash):
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

    def get_only_ipfs_hash(self, path, is_hidden=True) -> str:
        """Get only chunk and hash of a given path, do not write to disk.

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

    def connect_to_bootstrap_node(self):
        """Connect into return addresses of the currently connected peers."""
        if not is_ipfs_on():
            raise IpfsNotConnected

        # cmd = ["ipfs", "bootstrap", "list"]
        # output = run(cmd)
        # s = StringIO(output)
        peers = self.client.bootstrap.list()["Peers"]
        peer_address = None
        for peer in peers:
            if re.search(r"/ip4/", peer) is not None:
                peer_address = peer
                break
        else:
            return False

        print(f"==> Trying to connect into {peer_address} using swarm connect")
        output = self.client.swarm.connect(peer_address)
        if ("connect" and "success") in str(output):
            log(str(output), "bold green")
            return True

        return False

    def get_ipfs_id(self, client) -> str:
        """Return public ipfs id."""
        ipfs_addresses = client.id()["Addresses"]
        for ipfs_address in reversed(ipfs_addresses):
            if "::" not in ipfs_address:
                if "127.0.0.1" in ipfs_address:
                    log(f"==> {ipfs_address}")
                else:
                    log(f"==> ipfs_id={ipfs_address}")
                    return ipfs_address

        raise ValueError("No valid ipfs has is found")
