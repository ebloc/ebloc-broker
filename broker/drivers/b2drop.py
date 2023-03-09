#!/usr/bin/env python3

import fnmatch
import json
import os
import shutil
import sys
import time
from contextlib import suppress
from pathlib import Path
from typing import List

from broker import cfg, config
from broker._utils._log import br, log, ok
from broker._utils.tools import _remove, bytes_to_mb, mkdir, read_json
from broker.config import env
from broker.drivers.storage_class import Storage
from broker.lib import run
from broker.utils import CacheType, StorageID, cd, generate_md5sum, get_date, print_tb, untar

Ebb = cfg.Ebb


class B2dropClass(Storage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.share_token = None
        self.accept_flag = 0
        self.share_id = {}
        self.tar_downloaded_path = {}
        self.code_hashes_to_process: List[str] = []
        for source_code_hash in self.code_hashes:
            self.code_hashes_to_process.append(cfg.w3.toText(source_code_hash))

        for source_code_hash in self.code_hashes_to_process:
            self.check_already_cached(source_code_hash)

    def cache_wrapper(self) -> bool:
        for idx, folder_name in enumerate(self.code_hashes_to_process):
            if self.cloudStorageID[idx] == StorageID.NONE:
                return True
            elif not self.cache(folder_name, idx):
                return False
        return True

    def search_token(self, f_id, share_list, folder_name, is_verbose=False) -> bool:
        """Search for the share_token from the shared folder."""
        f_id = f_id.replace("@b2drop.eudat.eu", "")  # check in case
        share_key = f"{folder_name}_{self.requester_id[:16]}"
        if not is_verbose:
            log(f"## searching share tokens for the related source_code_folder={share_key}")

        for idx in range(len(share_list) - 1, -1, -1):
            # starts iterating from last item to the first one
            input_folder_name = share_list[idx]["name"]
            input_folder_name = input_folder_name[1:]  # removes '/' at the beginning
            share_id = share_list[idx]["id"]
            user = share_list[idx]["user"]
            if input_folder_name == share_key and user == f_id:
                self.share_token = str(share_list[idx]["share_token"])
                self.share_id[share_key] = {
                    "share_id": int(share_id),
                    "share_token": self.share_token,
                }
                if Ebb.mongo_broker.add_item_share_id(share_key, share_id, self.share_token):
                    log(f"#> Added into mongoDB {ok()}")
                else:
                    log("E: Something is wrong, not added into mongoDB")

                log(f"==> name={folder_name} | share_id={share_id} | share_token={self.share_token} {ok()}")
                try:
                    config.oc.accept_remote_share(int(share_id))
                    log(f"## share_id={share_id} is accepted")
                except Exception as e:
                    print_tb(e)

                self.accept_flag += 1
                return True

        return False

    def cache(self, folder_name, _id) -> bool:
        is_cache_success = self._is_cached(folder_name, _id)
        cache_folder = Path()
        if self.cache_type[_id] == CacheType.PRIVATE:
            # download into private directory of the user
            cache_folder = self.private_dir
        elif self.cache_type[_id] == CacheType.PUBLIC:
            cache_folder = self.public_dir

        cached_tar_fn = cache_folder / f"{folder_name}.tar.gz"
        if is_cache_success:
            self.folder_type_dict[folder_name] = "tar.gz"
            self.tar_downloaded_path[folder_name] = cached_tar_fn
            return True

        if not os.path.isfile(cached_tar_fn):
            if os.path.isfile(cache_folder / f"{folder_name}.tar.gz"):
                tar_hash = generate_md5sum(f"{cache_folder}/{folder_name}.tar.gz")
                if tar_hash == folder_name:
                    # checking is already downloaded folder's hash matches with the given hash
                    self.folder_type_dict[folder_name] = "folder"
                    log(f"==> {folder_name} is already cached under the public directory", "bg")
                    return True
                self.folder_type_dict[folder_name] = "tar.gz"
                try:
                    self.download_folder(cache_folder, folder_name)
                except Exception as e:
                    print_tb(e)
                    self.full_refund()
                    return False
            else:
                self.folder_type_dict[folder_name] = "tar.gz"
                try:
                    self.download_folder(cache_folder, folder_name)
                except Exception as e:
                    print_tb(e)
                    self.full_refund()
                    return False

            if (
                _id == 0
                and self.folder_type_dict[folder_name] == "tar.gz"
                and not self.is_run_exists_in_tar(cached_tar_fn)
            ):
                _remove(cached_tar_fn)
                return False
        else:  # here we already know that its tar.gz file
            self.folder_type_dict[folder_name] = "tar.gz"
            if generate_md5sum(cached_tar_fn) == folder_name:
                # checking is already downloaded folder's hash matches with the given hash
                log(f"==> {cached_tar_fn} is already cached", "bg")
                self.tar_downloaded_path[folder_name] = cached_tar_fn
                self.folder_type_dict[folder_name] = "tar.gz"
                return True

            try:
                self.download_folder(cache_folder, folder_name)
            except Exception as e:
                print_tb(e)
                self.full_refund()
                return False

        return True

    def _download_folder(self, results_folder_prev, folder_name):
        """Download corresponding folder from the B2DROP.

        Always assumes job is submitted as .tar.gz file
        """
        cached_tar_fn = f"{results_folder_prev}/{folder_name}.tar.gz"
        log("#> downloading [g]output.zip[/g] for:", end="")
        log(f"{folder_name} => {cached_tar_fn} ", "bold")
        key = folder_name
        share_key = f"{folder_name}_{self.requester_id[:16]}"
        for attempt in range(1):
            try:
                log("==> Trying [blue]wget[/blue] approach...")
                token = self.share_id[share_key]["share_token"]
                if token:
                    download_fn = f"{cached_tar_fn.replace('.tar.gz', '')}_{self.requester_id}.download"
                    cmd = [
                        "wget",
                        "-O",
                        download_fn,
                        "-c",
                        f"https://b2drop.eudat.eu/s/{token}/download",
                        "-q",
                        "--show-progres",
                        "--progress=bar:force",
                    ]
                    log(" ".join(cmd), is_code=True, color="bold yellow")
                    run(cmd)
                    with cd(results_folder_prev):
                        run(["unzip", "-o", "-j", download_fn])

                    _remove(download_fn)
                    self.tar_downloaded_path[folder_name] = cached_tar_fn
                    log(f"## download file from B2DROP{ok()}")
                    return
            except:
                log("E: Failed to download B2DROP file via wget.\nTrying `config.oc.get_file()` approach...")
                if config.oc.get_file(f"/{key}/{folder_name}.tar.gz", cached_tar_fn):
                    self.tar_downloaded_path[folder_name] = cached_tar_fn
                    log(ok())
                    return
                else:
                    log(f"E: Something is wrong, oc could not retrieve the file [attempt:{attempt}]")

        raise Exception("b2drop download error")

    def download_folder(self, cache_folder, folder_name):
        """Wrap download folder function."""
        self._download_folder(cache_folder, folder_name)
        self.check_downloaded_folder_hash(cache_folder / f"{folder_name}.tar.gz", folder_name)

    def accept_given_shares(self):
        for *_, v in self.share_id.items():
            try:
                config.oc.accept_remote_share(int(v["share_id"]))
            except Exception as e:
                print_tb(e)

    def get_file_size(self, fn, folder_name):
        # accept_given_shares()
        try:
            log(f"## trying to get {fn} file info from B2DROP")
            #: DAV/Properties/getcontentlength the number of bytes of a resource
            return config.oc.file_info(fn).get_size()
        except Exception as e:
            log(f"warning: {e}")
            if "HTTP error: 404" in str(e):
                try:
                    _folder_fn = folder_name
                    _list = fnmatch.filter(os.listdir(env.OWNCLOUD_PATH), f"{_folder_fn} *")
                    for _dir in _list:
                        shutil.move(f"{env.OWNCLOUD_PATH}/{_dir}", f"{env.OWNCLOUD_PATH}/{_folder_fn}")

                    return config.oc.file_info(fn).get_size()
                except Exception as e:
                    log(f"E: {e}")
                    _list = config.oc.list(".")
                    for path in _list:
                        if folder_name in path.get_name() and folder_name != path.get_name:
                            config.oc.move(path.get_name(), folder_name)

                return config.oc.file_info(fn).get_size()

            log(str(e))
            raise Exception("failed all the attempts to get file info at B2DROP") from e

    def total_size_to_download(self) -> None:
        data_transfer_in_to_download = 0  # total size to download in bytes
        for idx, source_code_hash_text in enumerate(self.code_hashes_to_process):
            if self.cloudStorageID[idx] != StorageID.NONE:
                folder_name = source_code_hash_text
                if folder_name not in self.is_cached:
                    data_transfer_in_to_download += self.get_file_size(
                        f"/{folder_name}/{folder_name}.tar.gz", folder_name
                    )

        self.data_transfer_in_to_download_mb = bytes_to_mb(data_transfer_in_to_download)
        log(
            f"## total size to download {data_transfer_in_to_download} bytes == "
            f"{self.data_transfer_in_to_download_mb} MB"
        )

    def get_share_token(self, f_id):
        """Check key is already shared or not."""
        folder_token_flag = {}
        if not os.path.isdir(self.private_dir):
            raise Exception(f"{self.private_dir} does not exist")

        share_id_file = f"{self.private_dir}/{self.job_key}_share_id.json"
        for idx, source_code_hash_text in enumerate(self.code_hashes_to_process):
            if self.cloudStorageID[idx] != StorageID.NONE:
                folder_name = source_code_hash_text
                self.folder_type_dict[folder_name] = None
                source_fn = f"{folder_name}/{folder_name}.tar.gz"
                if os.path.isdir(env.OWNCLOUD_PATH / f"{folder_name}"):
                    log(
                        f"## B2DROP shared folder({folder_name}) is already accepted and "
                        "exists on the B2DROP's mounted folder"
                    )
                    if os.path.isfile(f"{env.OWNCLOUD_PATH}/{source_fn}"):
                        self.folder_type_dict[folder_name] = "tar.gz"
                    else:
                        self.folder_type_dict[folder_name] = "folder"

                try:
                    info = config.oc.file_info(f"/{source_fn}")
                    log("shared folder is already accepted")
                    size = info.attributes["{DAV:}getcontentlength"]
                    folder_token_flag[folder_name] = True
                    log(f"==> index={br(idx)}: /{source_fn} => {size} bytes")
                except:
                    log(f"warning: shared_folder{br(source_code_hash_text, 'green')} is not accepted yet")
                    folder_token_flag[folder_name] = False

        with suppress(Exception):
            data = read_json(share_id_file)
            if isinstance(data, dict) and bool(data):
                self.share_id = data

        if self.share_id:
            log("==> share_id:")
            log(self.share_id, "bold")

        for share_key, value in self.share_id.items():  # there is only single item
            try:
                # TODO: if added before or some do nothing
                if Ebb.mongo_broker.add_item_share_id(share_key, value["share_id"], value["share_token"]):
                    # adding into mongoDB for future usage
                    log(f"#> [g]{share_key}[/g] is added into mongoDB{ok()}")
            except Exception as e:
                print_tb(e)
                log(f"E: {e}")

        for attempt in range(cfg.RECONNECT_ATTEMPTS):
            try:
                share_list = config.oc.list_open_remote_share()
                break
            except Exception as e:
                log(f"E: Failed to list_open_remote_share B2DROP [attempt={attempt}]")
                print_tb(e)
                time.sleep(1)
            else:
                break
        else:
            return False

        self.accept_flag = 0
        for idx, source_code_hash_text in enumerate(self.code_hashes_to_process):
            if self.cloudStorageID[idx] == StorageID.NONE:
                self.accept_flag += 1
            else:
                # folder should not be registered data on the provider
                #: search_token is priority
                if not self.search_token(f_id, share_list, source_code_hash_text):
                    try:
                        share_key = f"{source_code_hash_text}_{self.requester_id[:16]}"
                        shared_id = Ebb.mongo_broker.find_shareid_item(key=share_key)
                        self.share_id[share_key] = {
                            "share_id": shared_id["share_id"],
                            "share_token": shared_id["share_token"],
                        }
                        self.accept_flag += 1
                    except Exception as e:
                        if "warning: " not in str(e):
                            log(f"E: {e}")
                        else:
                            log(str(e))

                        if folder_token_flag[folder_name] and bool(self.share_id):
                            self.accept_flag += 1
                        else:
                            self.search_token(f_id, share_list, folder_name)

                if self.accept_flag is len(self.code_hashes):
                    break
        else:
            if self.accept_flag is len(self.code_hashes):
                log("shared token already exists on mongoDB")
            # else:
            #     raise Exception(f"could not find a shared file. Found ones are:\n{self.share_id}")

        if bool(self.share_id):
            with open(share_id_file, "w") as f:
                json.dump(self.share_id, f)
        else:
            raise Exception("share_id is empty")

        # self.total_size_to_download()

    def run(self) -> bool:
        self.start_timestamp = time.time()
        if cfg.IS_THREADING_ENABLED:
            self.thread_log_setup()
            log(f"## Keep track from: tail -f {self.drivers_log_path}")

        try:
            log(f" * log_path={self.drivers_log_path}")
            self._run()
            # self.thread_log_setup()
            return True
        except Exception as e:
            print_tb(f"{self.job_key}_{self.index} {e}")
            sys.exit(1)
        finally:
            time.sleep(0.25)

    def _run(self) -> bool:
        log(f"{br(get_date())} new job has been received through B2DROP: {self.job_key} {self.index} ", "bold cyan")
        # TODO: refund check
        try:
            provider_info = Ebb.get_provider_info(self.logged_job.args["provider"])
            self.get_share_token(provider_info["f_id"])
        except Exception as e:
            print_tb(f"E: could not get the share id. {e}")
            # return False ###

        if int(self.data_transfer_in_to_download_mb) > int(self.data_transfer_in_requested):
            log(f" * data_transfer_in_to_download_MB={self.data_transfer_in_to_download_mb}")
            log(f" * data_transfer_in_requested={self.data_transfer_in_requested}")
            log("E: Requested size to download the source code and data files is greater than the given amount")
            return self.full_refund()

        if not self.cache_wrapper():
            return False

        for idx, folder_name in enumerate(self.code_hashes_to_process):
            if self.cloudStorageID[idx] != StorageID.NONE:
                if self.folder_type_dict[folder_name] == "tar.gz":
                    # untar the cached tar file into private directory
                    tar_to_extract = self.tar_downloaded_path[folder_name]
                    if self.job_key == folder_name:
                        target = self.results_folder
                    else:
                        target = f"{self.results_data_folder}/{folder_name}"
                        mkdir(target)

                    try:
                        untar(tar_to_extract, target)
                    except:
                        return False

                    if idx == 0 and not self.check_run_sh():
                        self.full_refund()
                        return False

        log(f" * data_transfer_in_requested={self.data_transfer_in_requested} MB")
        for idx, folder_name in enumerate(self.code_hashes_to_process):
            if self.cloudStorageID[idx] == StorageID.NONE:
                if isinstance(folder_name, bytes):
                    self.registered_data_hashes.append(folder_name.decode("utf-8"))
                else:
                    self.registered_data_hashes.append(folder_name)
            else:
                share_key = f"{folder_name}_{self.requester_id[:16]}"
                try:
                    self.share_id[share_key]["share_token"]  # noqa
                except KeyError:
                    try:
                        shared_id = Ebb.mongo_broker.find_shareid_item(key=share_key)
                        log(f"#> reading from mongo_broker{ok()}")
                        log(shared_id)
                    except Exception as e:
                        print_tb(e)
                        log(f"E: [yellow]share_id[/yellow] cannot be detected from the key={share_key}")
                        return False

        return self.sbatch_call()
