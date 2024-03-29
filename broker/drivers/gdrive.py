#!/usr/bin/env python3

import os
import subprocess
import time
from contextlib import suppress

from broker import cfg
from broker._utils._log import WHERE, br
from broker._utils.tools import _remove, mkdir
from broker.config import env
from broker.drivers.storage_class import Storage
from broker.lib import calculate_size, echo_grep_awk, log, run, subprocess_call
from broker.libs import _git, gdrive
from broker.utils import CacheID, StorageID, byte_to_mb, generate_md5sum, get_date, popen_communicate, print_tb, untar


class GdriveClass(Storage):
    def _download_folder(self, name, key, code_hash, _id, cache_folder) -> None:
        if self._is_cached(code_hash, _id):
            return

        is_continue = False
        with suppress(Exception):
            output = self.job_infos[0]["storage_duration"][_id]
            is_continue = True

        if is_continue and not self.job_infos[0]["is_cached"][code_hash] and not output:
            log("==> Downloaded as temporary data file", "yellow")
            self.folder_path_to_download[code_hash] = self.results_folder_prev
        else:
            self.folder_path_to_download[code_hash] = cache_folder
            # self.assign_folder_path_to_download(_id, code_hash, cache_folder)

        log(f"==> downloading => {key}\nPath to download => {self.folder_path_to_download[code_hash]}")
        if self.folder_type_dict[code_hash] == "folder":
            try:
                folder = self.folder_path_to_download[code_hash]
                subprocess_call(
                    ["gdrive", "download", "--recursive", key, "--force", "--path", folder],
                    10,
                )
            except Exception as e:
                raise e

            downloaded_folder_path = f"{self.folder_path_to_download[code_hash]}/{name}"
            if not os.path.isdir(downloaded_folder_path):
                # check before move operation
                raise Exception(f"folder ({downloaded_folder_path}) is not downloaded successfully")

            self.data_transfer_in_requested = calculate_size(downloaded_folder_path)
        else:
            try:
                folder = self.folder_path_to_download[code_hash]
                cmd = ["gdrive", "download", key, "--force", "--path", folder]
                subprocess_call(cmd, 10)
            except Exception as e:
                raise e

            file_path = f"{self.folder_path_to_download[code_hash]}/{name}"
            if not os.path.isfile(file_path):
                raise Exception(f"{WHERE(1)} E: File {file_path} is not downloaded successfully")

            link_path = f"{self.folder_path_to_download[code_hash]}/{name}"
            p1 = subprocess.Popen(["ls", "-ln", link_path], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(["awk", "{print $5}"], stdin=p1.stdout, stdout=subprocess.PIPE)
            p1.stdout.close()  # type: ignore
            # returns downloaded files size in bytes
            self.data_transfer_in_requested = byte_to_mb(p2.communicate()[0].decode("utf-8").strip())

        log(
            f"downloaded_data_transfer_in={self.data_transfer_in_requested} MB | "
            f"rounded={int(self.data_transfer_in_requested)} MB"
        )
        self.data_transfer_in_to_download_mb += self.data_transfer_in_requested

    def download_folder(self, name, key, code_hash, _id, cache_folder) -> None:
        self._download_folder(name, key, code_hash, _id, cache_folder)
        self.check_downloaded_folder_hash(cache_folder / name, code_hash)

    def assign_folder_path_to_download(self, _id, code_hash, path):
        if self.cache_type[_id] == CacheID.PUBLIC:
            self.folder_path_to_download[code_hash] = path
        elif self.cache_type[_id] == CacheID.PRIVATE:
            self.folder_path_to_download[code_hash] = self.private_dir

    def cache(self, _id, name, code_hash, key, is_job_key) -> None:
        if _id == 0:
            if self.folder_type_dict[code_hash] == "folder":
                self.folder_type_dict[code_hash] = "gzip"

        self.check_already_cached(code_hash)
        if self.cache_type[_id] == CacheID.PRIVATE:
            # first checking does is already exist under public cache directory
            cache_folder = self.private_dir
            cached_tar_fn = cache_folder / name
            if self.folder_type_dict[code_hash] == "gzip":
                if os.path.isfile(cached_tar_fn):
                    self.job_infos[0]["is_cached"][code_hash] = True
                    self.assign_folder_path_to_download(_id, code_hash, cached_tar_fn)
                    output = generate_md5sum(cached_tar_fn)
                    if output != self.md5sum_dict[key]:
                        raise Exception("File's md5sum does not match with its orignal md5sum value")

                    if output == code_hash:
                        # checking is already downloaded folder's hash matches with the given hash
                        log(f"==> {name} is already cached within the private cache directory")
                        self.cache_type[_id] = CacheID.PRIVATE
                        return
                else:
                    self.download_folder(name, key, code_hash, _id, cache_folder)
            elif self.folder_type_dict[code_hash] == "folder":
                output = ""
                if os.path.isfile(cached_tar_fn):
                    self.job_infos[0]["is_cached"][code_hash] = True
                    self.assign_folder_path_to_download(_id, code_hash, cache_folder)
                    output = generate_md5sum(cached_tar_fn)
                elif os.path.isdir(cache_folder):
                    self.job_infos[0]["is_cached"][code_hash] = True
                    self.folder_path_to_download[code_hash] = cache_folder
                    output = generate_md5sum(cache_folder)

                if output == code_hash:
                    # checking is already downloaded folder's hash matches with the given hash
                    log(f"==> {name} is already cached within the private cache directory")
                    self.cache_type[_id] = CacheID.PRIVATE
                    return
                else:
                    self.download_folder(name, key, code_hash, _id, cache_folder)
        elif self.cache_type[_id] == CacheID.PUBLIC:
            cache_folder = self.public_dir
            cached_tar_fn = cache_folder / name
            if self.folder_type_dict[code_hash] == "gzip":
                if os.path.isfile(cached_tar_fn):
                    output = generate_md5sum(cached_tar_fn)
                    if output == code_hash:
                        # checking is already downloaded folder's hash matches with the given hash
                        self.folder_path_to_download[code_hash] = self.public_dir
                        log(f"==> {name} is already cached within the public cache directory")
                    else:
                        self.download_folder(name, key, code_hash, _id, cache_folder)
                else:
                    self.download_folder(name, key, code_hash, _id, cache_folder)
                    if is_job_key and not self.is_run_exists_in_tar(cached_tar_fn):
                        _remove(cached_tar_fn)
                        raise Exception
            elif self.folder_type_dict[code_hash] == "folder":
                tar_fn = cache_folder / code_hash / name
                if os.path.isfile(tar_fn):
                    output = generate_md5sum(tar_fn)
                    if output == code_hash:
                        # checking is already downloaded folder's hash matches with the given hash
                        self.folder_path_to_download[code_hash] = self.public_dir
                        log(f"==> {name} is already cached within the public cache directory")
                    else:
                        self.download_folder(name, key, code_hash, _id, f"{self.public_dir}/{name}")
                else:
                    self.download_folder(name, key, code_hash, _id, f"{self.public_dir}/{name}")

    def remove_downloaded_file(self, code_hash, _id, pathname):
        if not self.job_infos[0]["is_cached"][code_hash] and self.job_infos[0]["storage_duration"][_id]:
            _remove(pathname)

    def get_data_init(self, key, _id, is_job_key=False):
        try:
            cmd = ["gdrive", "info", "--bytes", key, "-c", env.GDRIVE_METADATA]
            _p, gdrive_output, *_ = popen_communicate(cmd)
            if _p.returncode != 0:
                raise Exception(gdrive_output)
        except Exception as e:
            raise e

        mime_type = gdrive.get_file_info(gdrive_output, _type="Mime")
        folder_name = gdrive.get_file_info(gdrive_output, _type="Name")
        log(f"==> mime_type=[m]{mime_type}")
        if is_job_key:
            # key for the sourceCode tar.gz file is obtained
            try:
                self.data_transfer_in_to_download, self.job_key_list, key = gdrive.size(
                    key,
                    mime_type,
                    folder_name,
                    gdrive_output,
                    self.results_folder_prev,
                    self.code_hashes,
                    self.job_infos[0]["is_cached"],
                )
            except Exception as e:
                print_tb(e)
                raise e

        return mime_type, folder_name

    def pre_data_check(self, key):
        if self.data_transfer_in_to_download > self.data_transfer_in_requested:
            # TODO: full refund
            raise Exception(
                "Requested size to download the source-code and data files is greater than the given amount"
            )

        try:
            cmd = ["gdrive", "info", "--bytes", key, "-c", env.GDRIVE_METADATA]
            return subprocess_call(cmd, 1)
        except Exception as e:
            # TODO: gdrive list --query "sharedWithMe"
            print_tb(e)
            raise e

    def get_data(self, key, _id, is_job_key=False):
        try:
            mime_type, name = self.get_data_init(key, _id, is_job_key)
        except Exception as e:
            print_tb(e)
            raise e

        if is_job_key:
            gdrive_info = self.pre_data_check(key)
            name = gdrive.get_file_info(gdrive_info, "Name")
            mime_type = gdrive.get_file_info(gdrive_info, "Mime")

        # folder is already stored by its code_hash
        code_hash = name.replace(".tar.gz", "")
        log(f"==> name={name}")
        log(f"==> mime_type=[m]{mime_type}")
        if _id == 0:
            # source code folder, ignore downloading result-*
            name = f"{name}.tar.gz"
            try:
                output = gdrive.get_file_id(key)
            except Exception as e:
                print_tb(e)
                raise e

            key = echo_grep_awk(output, name, "1")
            mime_type = "gzip"

        if "gzip" in mime_type:
            try:
                cmd = ["gdrive", "info", "--bytes", key, "-c", env.GDRIVE_METADATA]
                gdrive_info = subprocess_call(cmd, 10)
            except Exception as e:
                print_tb(e)
                raise e

            code_hash = gdrive.get_file_info(gdrive_info, "Md5sum")
            self.md5sum_dict[key] = code_hash
            log(f"==> md5sum={self.md5sum_dict[key]}")
            # recieved job is in folder tar.gz
            self.folder_type_dict[code_hash] = "gzip"
            try:
                self.cache(_id, name, code_hash, key, is_job_key)
            except Exception as e:
                print_tb(e)
                raise e

            if is_job_key:
                target = self.results_folder
            else:
                target = f"{self.results_data_folder}/{code_hash}"
                mkdir(target)

            try:
                cache_folder = self.folder_path_to_download[code_hash]
                untar(f"{cache_folder}/{name}", target)
                return target
            except Exception as e:
                print_tb(e)
                raise e

            self.remove_downloaded_file(code_hash, _id, f"{cache_folder}/{name}")
        elif "folder" in mime_type:
            #: received job is in folder format
            self.folder_type_dict[code_hash] = "folder"
            try:
                self.cache(_id, name, code_hash, key, is_job_key)
            except Exception as e:
                raise e

            cache_folder = self.folder_path_to_download[code_hash]
            try:
                run(
                    [
                        "rsync",
                        "-avq",
                        "--partial-dir",
                        "--omit-dir-times",
                        f"{cache_folder}/{name}/",
                        self.results_folder,
                    ]
                )
            except Exception as e:
                print_tb(e)
                raise e

            self.remove_downloaded_file(code_hash, _id, f"{cache_folder}/{name}/")
            try:
                tar_fn = f"{self.results_folder}/{name}.tar.gz"
                untar(tar_fn, self.results_folder)
                _remove(tar_fn)
                return target
            except Exception as e:
                print_tb(e)
                raise e
        else:
            raise Exception("Neither folder or gzip type is given")

    def run(self) -> bool:
        self.start_timestamp = time.time()
        if cfg.IS_THREADING_ENABLED:
            self.thread_log_setup()

        log(f"{br(get_date())} job's source code has been sent through GDRIVE", "bold cyan")
        # self.get_data_init(key=self.job_key, _id=0, is_job_key=True)
        try:
            if os.path.isdir(self.results_folder):
                # attempt to download the source code
                target = self.get_data(key=self.job_key, _id=0, is_job_key=True)

            if not os.path.isdir(f"{target}/.git"):
                # log(f"warning: .git folder does not exist within {target}")
                _git.generate_git_repo(target)
        except Exception as e:
            print_tb(e)
            return False

        if not self.check_run_sh():
            self.full_refund()

        for idx, code_hash in enumerate(self.code_hashes):
            if self.cloudStorageID[idx] == StorageID.NONE:
                if isinstance(code_hash, bytes):
                    self.registered_data_hashes.append(code_hash.decode("utf-8"))
                else:
                    self.registered_data_hashes.append(code_hash)

        for idx, (_, value) in enumerate(self.job_key_list.items()):
            try:
                target = self.get_data(value, idx + 1)
                if not os.path.isdir(f"{target}/.git"):
                    log(f"warning: .git folder does not exist within {target}")
                    _git.generate_git_repo(target)
            except:
                return False

        return self.sbatch_call()
