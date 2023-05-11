#!/usr/bin/env python3

import ipfshttpclient
import os
import re
import signal
import sys
import time
from cid import make_cid
from contextlib import suppress
from halo import Halo
from subprocess import check_output

from broker import cfg
from broker._utils._log import br, ok
from broker._utils.tools import _remove, constantly_print_popen, handler, log, print_tb
from broker.config import env
from broker.errors import IpfsNotConnected, QuietExit
from broker.lib import subprocess_call
from broker.utils import (
    _try,
    compress_folder,
    is_ipfs_on,
    popen_communicate,
    question_yes_no,
    raise_error,
    run,
    start_ipfs_daemon,
    untar,
)


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
    def get_only_ipfs_hash(self, path, is_hidden=True) -> str:
        """Get only chunk and hash of a given path, do not write to disk.

        :param str path: path: Path of a folder or file
        :returns: string that contains the ouput of the run commad.
        """
        if os.path.isdir(path):
            cmd = ["ipfs", "add", "-r", "--quieter", "--only-hash", path]
            if is_hidden:
                # include files that are hidden such as .git/
                # Only takes effect on recursive add
                cmd.insert(3, "--hidden")
        elif os.path.isfile(path):
            cmd = ["ipfs", "add", "--quieter", "--only-hash", path]
        else:
            raise Exception("Requested path does not exist")

        try:
            return _try(lambda: run(cmd))
        except Exception as e:
            raise e

    def is_valid(self, ipfs_hash: str) -> bool:
        try:
            make_cid(ipfs_hash)
            return True
        except:
            return False

    def is_hash_locally_cached(self, ipfs_hash: str, ipfs_refs_local=None) -> bool:
        """Return true if hash locally cached.

        Run `ipfs --offline refs -r` or `ipfs --offline block stat` etc even if your normal daemon is running.
        With that you can check if something is available locally or no.
        """
        if not ipfs_refs_local:
            ipfs_refs_local = run(["ipfs", "refs", "local"]).split("\n")

        for _hash in ipfs_refs_local:
            if ipfs_hash == _hash:
                return True

        return False

        # try:
        #     check_output(["ipfs", "--offline", "block", "stat", ipfs_hash], stderr=DEVNULL)
        #     return True
        # except:
        #     # log(f"E: [g]{e}")
        #     return False
        # TODO: check may return true even its not exist

    def pin(self, ipfs_hash: str) -> bool:
        return run(["ipfs", "pin", "add", ipfs_hash])

    def decrypt_using_gpg(self, gpg_file, extract_target=None):
        """Decrypt compresses file using gpg.

        This function is specific for using on driver.ipfs to decript tar file,
        specific for "tar.gz" file types.

        gpg --verbose --output={tar_fn} --pinentry-mode loopback \
            --passphrase-file=gpg_pass.txt --decrypt <gpg_file>
        """
        if not os.path.isfile(f"{gpg_file}.gpg"):
            os.symlink(gpg_file, f"{gpg_file}.gpg")

        gpg_file_link = f"{gpg_file}.gpg"
        tar_fn = f"{gpg_file}.tar.gz"
        try:
            cmd = [
                "gpg",
                "--verbose",
                "--batch",
                "--yes",
                f"--output={tar_fn}",
                "--pinentry-mode",
                "loopback",
                f"--passphrase-file={env.GPG_PASS_FILE}",
                "--decrypt",
                gpg_file_link,
            ]
            run(cmd, suppress_stderr=True)
            log(f"#> GPG decrypt {ok()}")
            _remove(gpg_file)
            os.unlink(gpg_file_link)
        except Exception as e:
            print_tb(e)
            raise e
        # finally:
        #     os.unlink(gpg_file_link)

        if extract_target:
            try:
                untar(tar_fn, extract_target)
            except Exception as e:
                raise Exception("Could not extract the given tar file") from e
            finally:
                cmd = None
                _remove(f"{extract_target}/.git")
                _remove(tar_fn)

    def remove_lock_files(self):
        for name in ["repo.lock", "datastore/LOCK"]:
            _remove(f"{env.HOME}/.ipfs/{name}")

    def gpg_encrypt(self, from_gpg_fingerprint, recipient_gpg_fingerprint, target):
        if from_gpg_fingerprint == recipient_gpg_fingerprint:
            raise Exception("E: Both given fingerprints are same")

        self.check_gpg_password(from_gpg_fingerprint)
        is_delete = False
        if os.path.isdir(target):
            try:
                *_, encrypt_target = compress_folder(target)
                encrypted_file_target = f"{encrypt_target}.gpg"
                is_delete = True
            except Exception as e:
                print_tb(e)
        else:
            if os.path.isfile(target):
                encrypt_target = target
                encrypted_file_target = f"{target}.gpg"
                is_delete = True
            else:
                log(f"E: {target} does not exist")

        if os.path.isfile(encrypted_file_target):
            log(f"## gpg_file: {encrypted_file_target} is already created")
            return encrypted_file_target

        for attempt in range(5):
            try:
                cmd = ["gpg", "--keyserver", "hkps://keyserver.ubuntu.com", "--recv-key", recipient_gpg_fingerprint]
                log(f"{br(attempt)} cmd: [w]{' '.join(cmd)}")
                run(cmd, suppress_stderr=True)  # this may not work if it is requested too much in short time
                break
            except Exception as e:
                log(f"warning: {e}")
                time.sleep(30)
        try:
            cmd = [
                "gpg",
                "--batch",
                "--yes",
                "--recipient",
                recipient_gpg_fingerprint,
                "--trust-model",
                "always",
                "--output",
                encrypted_file_target,
                "--encrypt",
                encrypt_target,
            ]
            run(cmd)
            log(f"==> gpg_file=[m]{encrypted_file_target}")
            return encrypted_file_target
        except Exception as e:
            print_tb(e)
            if "encryption failed: Unusable public key" in str(e):
                log("#> Check solution: https://stackoverflow.com/a/34132924/2402577")

            raise e
        finally:
            if is_delete:
                _remove(encrypt_target)

    ################
    # ONLINE CALLS #
    ################
    def swarm_connect(self, ipfs_address: str, is_verbose=False):
        """Swarm connect into the ipfs node."""
        if not is_ipfs_on():
            start_ipfs_daemon()
            if is_ipfs_on():
                raise IpfsNotConnected

        # TODO: check is valid IPFS id
        try:
            if is_verbose:
                log(f" * trying to connect into {ipfs_address}", end="")
            else:
                log(f" * trying to connect into {ipfs_address}")

            cmd = ["/usr/local/bin/ipfs", "swarm", "connect", ipfs_address]
            p, output, e = popen_communicate(cmd)
            if p.returncode != 0:
                e = e.replace("[/", "/").replace("]", "").replace("e: ", "").rstrip()
                if is_verbose:
                    log("  [  failed  ]")
                else:
                    log()
                    if "failure: dial to self attempted" in e:
                        log(f"E: [g]{e}")
                        if not cfg.IS_FULL_TEST and not question_yes_no("#> Would you like to continue?"):
                            raise QuietExit
                    else:
                        log("E: connection into provider's IPFS node via swarm is not accomplished.\nTry: nc <ip> 4001")
                        raise Exception(e)
            else:
                if is_verbose:
                    log(ok())
                else:
                    log(f"{output} {ok()}")
        except Exception as e:
            if is_verbose:
                log("[  failed  ]")

            if not is_verbose:
                print_tb(e)

            raise e

    def stat(self, ipfs_hash, _is_ipfs_on=True):
        """Return stat of the give IPFS hash.

        This function *may* run for an indetermined time. Returns a dict with the
        size of the block with the given hash.
        """
        if _is_ipfs_on:
            if not is_ipfs_on():
                start_ipfs_daemon()
                if is_ipfs_on():
                    raise IpfsNotConnected

        msg = f"$ ipfs object stat {ipfs_hash} --timeout={cfg.IPFS_TIMEOUT}s "
        with Halo(text=msg, spinner="line", placement="right"):
            return subprocess_call(["ipfs", "object", "stat", ipfs_hash, f"--timeout={cfg.IPFS_TIMEOUT}s"])

        log()

    def is_hash_exists_online(self, ipfs_hash: str, ipfs_address=None, is_verbose=False):
        log(f"## attempting to check IPFS file [g]{ipfs_hash}[/g] ... ")
        if not is_ipfs_on():
            start_ipfs_daemon()
            if is_ipfs_on():
                raise IpfsNotConnected

        if not cfg.IS_THREADING_ENABLED:
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(cfg.IPFS_TIMEOUT)  # Set the signal handler and a 300-second alarm

        try:
            if ipfs_address:
                with suppress(Exception):  # TODO: Attempt to swarm connect into requester
                    self.swarm_connect(ipfs_address, is_verbose=is_verbose)

            output = self.stat(ipfs_hash, _is_ipfs_on=False)
            _stat = {}
            for line in output.split("\n"):
                if "CumulativeSize" not in line:
                    line = line.replace(" ", "")
                    output_stat = line.split(":")
                    _stat[output_stat[0]] = int(output_stat[1])

            log("ipfs_object_stat=", end="")
            log(_stat, "b")
            cumulative_size = int(output.split("\n")[4].split(":")[1].replace(" ", ""))
            log(f"cumulative_size={cumulative_size}")
            return output, cumulative_size
        except Exception as e:
            raise Exception(f"Timeout, failed to find ipfs file: {ipfs_hash}") from e

    def get(self, ipfs_hash, path, is_storage_paid=False):
        if not is_ipfs_on():
            start_ipfs_daemon()
            if is_ipfs_on():
                raise IpfsNotConnected

        output = constantly_print_popen(["ipfs", "get", ipfs_hash, f"--output={path}"])
        log(output)
        if is_storage_paid:
            # pin downloaded ipfs hash if storage is paid
            output = check_output(["ipfs", "pin", "add", ipfs_hash]).decode("utf-8").rstrip()
            log(output)

    def get_cumulative_size(self, ipfs_hash: str):
        if not is_ipfs_on():
            start_ipfs_daemon()
            if is_ipfs_on():
                raise IpfsNotConnected

        output = self.stat(ipfs_hash)
        if output:
            return int(output.split("\n")[4].split(":")[1].replace(" ", ""))
        else:
            raise Exception(f"CumulativeSize could not found for {ipfs_hash}")

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
                result_ipfs_hash = constantly_print_popen(cmd)
                if not result_ipfs_hash and not self.is_valid(result_ipfs_hash):
                    log(f"E: Generated new hash returned empty. Trying again. Try count: {attempt}")
                    time.sleep(5)
                elif not self.is_valid(result_ipfs_hash):
                    log(f"E: Generated new hash is not valid. Trying again. Try count: {attempt}")
                    time.sleep(5)

                break
            except:
                log(f"E: Generated new hash returned empty. Trying again. Try count: {attempt}")
                time.sleep(5)
        else:
            raise Exception("Failed all the attempts to generate ipfs hash")

        return result_ipfs_hash

    def connect_to_bootstrap_node(self):
        """Connect into return addresses of the currently connected peers."""
        if not is_ipfs_on():
            start_ipfs_daemon()
            if is_ipfs_on():
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
            log(str(output), "bg")
            return True

        return False

    def get_ipfs_address(self, client=None) -> str:
        if self.client:
            _client = self.client
        else:
            _client = client

        """Return public ipfs id."""
        ipfs_addresses = _client.id()["Addresses"]
        for ipfs_address in reversed(ipfs_addresses):
            if "::" not in ipfs_address and "127.0.0.1" not in ipfs_address and "/tcp/" in ipfs_address:
                return ipfs_address

        for ipfs_address in reversed(ipfs_addresses):
            if "/ip4/127.0.0.1/tcp/4001/p2p/" in ipfs_address:
                return ipfs_address

        raise QuietExit("E: No valid ipfs address is found from output of `ipfs id`. Try opening port 4001")

    def check_gpg_password(self, gpg_fingerprint):
        """Check passphrase of gpg from a file.

        * How can I check passphrase of gpg from a file?
        __ https://unix.stackexchange.com/q/683084/198423
        """
        cmd = [
            "gpg",
            "--batch",
            "--pinentry-mode",
            "loopback",
            f"--passphrase-file={env.GPG_PASS_FILE}",
            "--dry-run",
            "--passwd",
            gpg_fingerprint,
        ]
        _p, output, error_msg = popen_communicate(cmd)  # type: ignore
        if _p.returncode or error_msg:
            raise Exception(error_msg)
            # raise BashCommandsException(p.returncode, output, error_msg, str(cmd))

        # try:
        #     run(cmd)
        # except Exception as e:
        #     print_tb(e)
        #     raise e

    def publish_gpg(self, gpg_fingerprint, is_verbose=True):
        # log("## running: gpg --verbose --keyserver hkps://keyserver.ubuntu.com --send-keys <key_id>")
        if is_verbose:
            run(["gpg", "--verbose", "--keyserver", "hkps://keyserver.ubuntu.com", "--send-keys", gpg_fingerprint])
        else:
            run(["gpg", "--keyserver", "hkps://keyserver.ubuntu.com", "--send-keys", gpg_fingerprint])

    def is_gpg_published(self, gpg_fingerprint):
        try:
            run(["gpg", "--list-keys", gpg_fingerprint])
        except Exception as e:
            try:
                self.publish_gpg(gpg_fingerprint)
            except:
                raise Exception from e

    def get_gpg_fingerprint(self, email) -> str:
        output = run(["gpg", "--list-secret-keys", "--keyid-format", "LONG", email])
        return output.split("\n")[1].replace(" ", "").upper()
