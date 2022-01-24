#!/usr/bin/env python3

import fnmatch
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import List

from broker import cfg, config
from broker._utils._log import br, log, ok
from broker._utils.tools import _remove, bytes_to_mb, mkdir, read_json
from broker.config import env, logging
from broker.drivers.storage_class import Storage
from broker.lib import run
from broker.utils import CacheType, StorageID, cd, generate_md5sum, get_time, print_tb, untar

Ebb = cfg.Ebb


class EudatClass(Storage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.share_token = None
        self.accept_flag = 0
        self.share_id = {}
        self.tar_downloaded_path = {}
        self.source_code_hashes_to_process: List[str] = []
        for source_code_hash in self.source_code_hashes:
            self.source_code_hashes_to_process.append(cfg.w3.toText(source_code_hash))

        for source_code_hash in self.source_code_hashes_to_process:
            self.check_already_cached(source_code_hash)

    def cache_wrapper(self) -> bool:
        for idx, folder_name in enumerate(self.source_code_hashes_to_process):
            if self.cloudStorageID[idx] == StorageID.NONE:
                return True
            elif not self.cache(folder_name, idx):
                return False
        return True

    def search_token(self, f_id, share_list, folder_name, is_silent=False) -> bool:
        """Search for the share_token from the shared folder."""
        share_key = f"{folder_name}_{self.requester_id[:16]}"
        if not is_silent:
            log(f"## searching share tokens for the related source_code_folder={folder_name}")

        for idx in range(len(share_list) - 1, -1, -1):
            # starts iterating from last item to the first one
            input_folder_name = share_list[idx]["name"]
            input_folder_name = input_folder_name[1:]  # removes '/' at the beginning
            share_id = share_list[idx]["id"]
            # input_owner = share_list[i]['owner']
            input_user = f"{share_list[idx]['user']}@b2drop.eudat.eu"
            if input_folder_name == share_key and input_user == f_id:
                self.share_token = str(share_list[idx]["share_token"])
                self.share_id[share_key] = {
                    "share_id": int(share_id),
                    "share_token": self.share_token,
                }
                if Ebb.mongo_broker.add_item_share_id(share_key, share_id, self.share_token):
                    # adding into mongoDB for future uses
                    log(f"#> Added into mongoDB {ok()}")
                else:
                    logging.error("E: Something is wrong, not added into mongoDB")

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
        success = self.is_cached(folder_name, _id)
        cached_folder = Path("")
        if self.cache_type[_id] == CacheType.PRIVATE:
            # download into private directory at $HOME/.ebloc-broker/cache
            cached_folder = self.private_dir
        elif self.cache_type[_id] == CacheType.PUBLIC:
            cached_folder = self.public_dir

        cached_tar_file = cached_folder / f"{folder_name}.tar.gz"
        if success:
            self.folder_type_dict[folder_name] = "tar.gz"
            self.tar_downloaded_path[folder_name] = cached_tar_file
            return True

        if not os.path.isfile(cached_tar_file):
            if os.path.isfile(cached_folder / f"{folder_name}.tar.gz"):
                tar_hash = generate_md5sum(f"{cached_folder}/{folder_name}.tar.gz")
                if tar_hash == folder_name:
                    # checking is already downloaded folder's hash matches with the given hash
                    self.folder_type_dict[folder_name] = "folder"
                    log(f"==> {folder_name} is already cached under the public directory", "bold blue")
                    return True

                self.folder_type_dict[folder_name] = "tar.gz"
                try:
                    self.eudat_download_folder(cached_folder, folder_name)
                except Exception as e:
                    print_tb(e)
                    self.complete_refund()
                    return False
            else:
                self.folder_type_dict[folder_name] = "tar.gz"
                try:
                    self.eudat_download_folder(cached_folder, folder_name)
                except Exception as e:
                    print_tb(e)
                    self.complete_refund()
                    return False

            if (
                _id == 0
                and self.folder_type_dict[folder_name] == "tar.gz"
                and not self.is_run_exists_in_tar(cached_tar_file)
            ):
                _remove(cached_tar_file)
                return False
        else:
            # Here we already know that its tar.gz file
            self.folder_type_dict[folder_name] = "tar.gz"
            output = generate_md5sum(cached_tar_file)
            if output == folder_name:
                # checking is already downloaded folder's hash matches with the given hash
                log(f"==> {cached_tar_file} is already cached")
                self.tar_downloaded_path[folder_name] = cached_tar_file
                self.folder_type_dict[folder_name] = "tar.gz"
                return True

            try:
                self.eudat_download_folder(cached_folder, folder_name)
            except Exception as e:
                print_tb(e)
                self.complete_refund()
                return False

        return True

    def eudat_download_folder(self, results_folder_prev, folder_name):
        """Download corresponding folder from the EUDAT.

        Always assumes job is sent as .tar.gz file
        """
        # TODO: check hash of the downloaded file is correct or not
        cached_tar_file = f"{results_folder_prev}/{folder_name}.tar.gz"
        log("#> downloading [green]output.zip[/green] for:", end="")
        log(f"{folder_name} => {cached_tar_file} ", "bold")
        key = folder_name
        share_key = f"{folder_name}_{self.requester_id[:16]}"
        for attempt in range(1):
            try:
                log("## Trying [blue]wget[/blue] approach...")
                token = self.share_id[share_key]["share_token"]
                if token:
                    download_fn = f"{cached_tar_file.replace('.tar.gz', '')}_{self.requester_id}.download"
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
                    log(" ".join(cmd), is_code=True, color="yellow")
                    run(cmd)
                    with cd(results_folder_prev):
                        run(["unzip", "-o", "-j", download_fn])

                    _remove(download_fn)
                    self.tar_downloaded_path[folder_name] = cached_tar_file
                    log(f"## download file from eudat {ok()}")
                    return
            except:
                log("E: Failed to download eudat file via wget.\nTrying config.oc.get_file() approach...")
                if config.oc.get_file(f"/{key}/{folder_name}.tar.gz", cached_tar_file):
                    self.tar_downloaded_path[folder_name] = cached_tar_file
                    log(ok())
                    return
                else:
                    logging.error(f"E: Something is wrong, oc could not retrieve the file [attempt:{attempt}]")

        raise Exception("Eudat download error")

    def accept_given_shares(self):
        for *_, v in self.share_id.items():
            try:
                config.oc.accept_remote_share(int(v["share_id"]))
            except Exception as e:
                print_tb(e)

    def get_file_size(self, fn, folder_name):
        # accept_given_shares()
        try:
            log(f"## trying to get {fn} info from EUDAT")
            #: DAV/Properties/getcontentlength the number of bytes of a resource
            info = config.oc.file_info(fn)
            return info.get_size()
        except Exception as e:
            log(f"warning: {e}")
            if "HTTP error: 404" in str(e):
                try:
                    _folder_fn = folder_name
                    _list = fnmatch.filter(os.listdir(env.OWNCLOUD_PATH), f"{_folder_fn} *")
                    for _dir in _list:
                        shutil.move(f"{env.OWNCLOUD_PATH}/{_dir}", f"{env.OWNCLOUD_PATH}/{_folder_fn}")

                    info = config.oc.file_info(fn)
                    return info.get_size()
                except Exception as e:
                    log(f"E: {e}")
                    _list = config.oc.list(".")
                    for path in _list:
                        if folder_name in path.get_name() and folder_name != path.get_name:
                            config.oc.move(path.get_name(), folder_name)

                info = config.oc.file_info(fn)
                return info.get_size()

            log(str(e))
            raise Exception("E: failed all the attempts to get file info at Eudat") from e

    def total_size_to_download(self):
        data_transfer_in_to_download = 0  # total size to download in bytes
        for idx, source_code_hash_text in enumerate(self.source_code_hashes_to_process):
            if self.cloudStorageID[idx] != StorageID.NONE:
                folder_name = source_code_hash_text
                if folder_name not in self.is_already_cached:
                    data_transfer_in_to_download += self.get_file_size(
                        f"/{folder_name}/{folder_name}.tar.gz", folder_name
                    )

        self.data_transfer_in_to_download_mb = bytes_to_mb(data_transfer_in_to_download)
        log(
            f"## Total size to download {data_transfer_in_to_download} bytes == "
            f"{self.data_transfer_in_to_download_mb} MB"
        )

    def eudat_get_share_token(self, f_id):
        """Check key is already shared or not."""
        folder_token_flag = {}
        if not os.path.isdir(self.private_dir):
            raise Exception(f"{self.private_dir} does not exist")

        share_id_file = f"{self.private_dir}/{self.job_key}_share_id.json"
        # accept_flag = 0 # TODO: delete it seems unneeded
        for idx, source_code_hash_text in enumerate(self.source_code_hashes_to_process):
            if self.cloudStorageID[idx] != StorageID.NONE:
                folder_name = source_code_hash_text
                self.folder_type_dict[folder_name] = None
                source_fn = f"{folder_name}/{folder_name}.tar.gz"
                if os.path.isdir(env.OWNCLOUD_PATH / f"{folder_name}"):
                    log(
                        f"## eudat shared folder({folder_name}) is already accepted and "
                        "exists on the eudat's mounted folder"
                    )
                    if os.path.isfile(f"{env.OWNCLOUD_PATH}/{source_fn}"):
                        self.folder_type_dict[folder_name] = "tar.gz"
                    else:
                        self.folder_type_dict[folder_name] = "folder"

                try:
                    info = config.oc.file_info(f"/{source_fn}")
                    logging.info("shared folder is already accepted")
                    size = info.attributes["{DAV:}getcontentlength"]
                    folder_token_flag[folder_name] = True
                    log(f"==> index={br(idx)}: /{source_fn} => {size} bytes")
                    # accept_flag += 1  # TODO: delete it seems unneeded
                except:
                    log(f"warning: shared_folder{br(source_code_hash_text, 'green')} is not accepted yet")
                    folder_token_flag[folder_name] = False

        try:  # TODO: add pass on template
            data = read_json(share_id_file)
            if isinstance(data, dict) and bool(data):
                self.share_id = data
        except:
            pass

        if self.share_id:
            log("==> share_id:")
            log(self.share_id, "bold")

        for share_key, value in self.share_id.items():  # there is only single item
            try:
                # TODO: if added before or some do nothing
                if Ebb.mongo_broker.add_item_share_id(share_key, value["share_id"], value["share_token"]):
                    # adding into mongoDB for future usage
                    log(f"#> [green]{share_key}[/green] is added into mongoDB {ok()}")
            except Exception as e:
                print_tb(e)
                log(f"E: {e}")

        for attempt in range(config.RECONNECT_ATTEMPTS):
            try:
                share_list = config.oc.list_open_remote_share()
                break
            except Exception as e:
                log(f"E: Failed to list_open_remote_share eudat [attempt={attempt}]")
                print_tb(e)
                time.sleep(1)
            else:
                break
        else:
            return False

        self.accept_flag = 0
        for idx, source_code_hash_text in enumerate(self.source_code_hashes_to_process):
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

                if self.accept_flag is len(self.source_code_hashes):
                    break
        else:
            if self.accept_flag is len(self.source_code_hashes):
                logging.info("shared token already exists on mongoDB")
            # else:
            #     raise Exception(f"E: could not find a shared file. Found ones are:\n{self.share_id}")

        if bool(self.share_id):
            with open(share_id_file, "w") as f:
                json.dump(self.share_id, f)
        else:
            raise Exception(f"E: share_id is empty")

        # self.total_size_to_download()

    def run(self) -> bool:
        self.start_time = time.time()
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
        log(f"{br(get_time())} new job has been received through EUDAT: {self.job_key} {self.index} ", "bold cyan")
        # TODO: refund check
        try:
            provider_info = Ebb.get_provider_info(self.logged_job.args["provider"])
            self.eudat_get_share_token(provider_info["f_id"])
        except Exception as e:
            print_tb(f"E: could not get the share id. {e}")
            # return False ###

        if int(self.data_transfer_in_to_download_mb) > int(self.data_transfer_in_requested):
            log(f"==> data_transfer_in_to_download_MB={self.data_transfer_in_to_download_mb}")
            log(f"==> data_transfer_in_requested={self.data_transfer_in_requested}")
            log("E: Requested size to download the source code and data files is greater than the given amount")
            return self.complete_refund()

        if not self.cache_wrapper():
            return False

        for idx, folder_name in enumerate(self.source_code_hashes_to_process):
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
                        self.complete_refund()
                        return False

        log(f"==> data_transfer_in_requested={self.data_transfer_in_requested} MB")
        for idx, folder_name in enumerate(self.source_code_hashes_to_process):
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
                        log(f"#> reading from mongo_broker {ok()}")
                        log(shared_id)
                    except Exception as e:
                        print_tb(e)
                        log(f"E: [yellow]share_id[/yellow] cannot be detected from key={share_key}")
                        return False

        return self.sbatch_call()
