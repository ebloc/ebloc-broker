#!/usr/bin/env python3

import os
import subprocess
import time

import broker.libs.gdrive as gdrive
import broker.libs.git as git
from broker._utils._log import br
from broker._utils.tools import mkdir
from broker.config import env, logging
from broker.drivers.storage_class import Storage
from broker.lib import calculate_folder_size, echo_grep_awk, log, run, subprocess_call
from broker.utils import WHERE, CacheType, _remove, byte_to_mb, generate_md5sum, get_time, print_tb, untar


class GdriveClass(Storage):
    def assign_folder_path_to_download(self, _id, source_code_hash, path):
        if self.cache_type[_id] == CacheType.PUBLIC:
            self.folder_path_to_download[source_code_hash] = path
        elif self.cache_type[_id] == CacheType.PRIVATE:
            self.folder_path_to_download[source_code_hash] = self.private_dir

    def cache(self, _id, name, source_code_hash, key, is_job_key) -> None:
        if _id == 0:
            if self.folder_type_dict[source_code_hash] == "folder":
                self.folder_type_dict[source_code_hash] = "gzip"

        self.check_already_cached(source_code_hash)
        if self.cache_type[_id] == CacheType.PRIVATE:
            # first checking does is already exist under public cache directory
            cache_folder = f"{self.private_dir}"
            cached_tar_file = f"{cache_folder}/{name}"
            if self.folder_type_dict[source_code_hash] == "gzip":
                if os.path.isfile(cached_tar_file):
                    self.is_already_cached[source_code_hash] = True
                    self.assign_folder_path_to_download(_id, source_code_hash, cached_tar_file)
                    output = generate_md5sum(cached_tar_file)
                    if output != self.md5sum_dict[key]:
                        raise Exception("File's md5sum does not match with its orignal md5sum value")

                    if output == source_code_hash:
                        # checking is already downloaded folder's hash matches with the given hash
                        log(f"==> {name} is already cached within private cache directory")
                        self.cache_type[_id] = CacheType.PRIVATE
                        return
                else:
                    if not self.gdrive_download_folder(name, key, source_code_hash, _id, cache_folder):
                        raise
            elif self.folder_type_dict[source_code_hash] == "folder":
                output = ""
                if os.path.isfile(cached_tar_file):
                    self.is_already_cached[source_code_hash] = True
                    self.assign_folder_path_to_download(_id, source_code_hash, cache_folder)
                    output = generate_md5sum(cached_tar_file)
                elif os.path.isdir(cache_folder):
                    self.is_already_cached[source_code_hash] = True
                    self.folder_path_to_download[source_code_hash] = cache_folder
                    output = generate_md5sum(cache_folder)

                if output == source_code_hash:
                    # checking is already downloaded folder's hash matches with the given hash
                    log(f"==> {name} is already cached within the private cache directory")
                    self.cache_type[_id] = CacheType.PRIVATE
                    return
                else:
                    if not self.gdrive_download_folder(name, key, source_code_hash, _id, cache_folder):
                        raise
        elif self.cache_type[_id] == CacheType.PUBLIC:
            cache_folder = self.public_dir
            cached_tar_file = f"{cache_folder}/{name}"
            if self.folder_type_dict[source_code_hash] == "gzip":
                if not os.path.isfile(cached_tar_file):
                    if not self.gdrive_download_folder(name, key, source_code_hash, _id, cache_folder):
                        raise

                    if is_job_key and not self.is_run_exists_in_tar(cached_tar_file):
                        _remove(cached_tar_file)
                        raise
                else:
                    output = generate_md5sum(cached_tar_file)
                    if output == source_code_hash:
                        # checking is already downloaded folder's hash matches with the given hash
                        self.folder_path_to_download[source_code_hash] = self.public_dir
                        log(f"==> {name} is already cached within public cache directory")
                    else:
                        if not self.gdrive_download_folder(name, key, source_code_hash, _id, cache_folder):
                            raise
            elif self.folder_type_dict[source_code_hash] == "folder":
                tar_file = f"{cache_folder}/{source_code_hash}/{name}"
                if os.path.isfile(tar_file):
                    output = generate_md5sum(tar_file)
                    if output == source_code_hash:
                        # checking is already downloaded folder's hash matches with the given hash
                        self.folder_path_to_download[source_code_hash] = self.public_dir
                        log(f"==> {name} is already cached within public cache directory")
                    else:
                        if not self.gdrive_download_folder(
                            name, key, source_code_hash, _id, f"{self.public_dir}/{name}"
                        ):
                            raise
                else:
                    if not self.gdrive_download_folder(name, key, source_code_hash, _id, f"{self.public_dir}/{name}"):
                        raise

    def gdrive_download_folder(self, name, key, source_code_hash, _id, cache_folder) -> bool:
        log(f"{WHERE(1)}")
        success = self.is_cached(source_code_hash, _id)
        if success:
            return True

        if not self.is_already_cached[source_code_hash] and not self.jobInfo[0]["storageDuration"][_id]:
            log("Downloaded as temporary data file", "yellow")
            self.folder_path_to_download[source_code_hash] = self.results_folder_prev
        else:
            self.folder_path_to_download[source_code_hash] = cache_folder
            # self.assign_folder_path_to_download(_id, source_code_hash, cache_folder)

        logging.info(f"Downloading => {key}\nPath to download => {self.folder_path_to_download[source_code_hash]}")
        if self.folder_type_dict[source_code_hash] == "folder":
            try:
                folder = self.folder_path_to_download[source_code_hash]
                subprocess_call(
                    ["gdrive", "download", "--recursive", key, "--force", "--path", folder],
                    10,
                )
            except:
                return False

            downloaded_folder_path = f"{self.folder_path_to_download[source_code_hash]}/{name}"
            if not os.path.isdir(downloaded_folder_path):
                # check before move operation
                logging.error(f"E: Folder ({downloaded_folder_path}) is not downloaded successfully")
                return False
            else:
                self.data_transfer_in_requested = calculate_folder_size(downloaded_folder_path)
                logging.info(
                    f"data_transfer_in_requested={self.data_transfer_in_requested} MB | "
                    f"Rounded={int(self.data_transfer_in_requested)} MB"
                )
        else:
            try:
                folder = self.folder_path_to_download[source_code_hash]
                cmd = ["gdrive", "download", key, "--force", "--path", folder]
                subprocess_call(cmd, 10)
            except:
                return False

            file_path = f"{self.folder_path_to_download[source_code_hash]}/{name}"
            if not os.path.isfile(file_path):
                logging.error(f"{WHERE(1)} E: File {file_path} is not downloaded successfully")
                return False

            filename = f"{self.folder_path_to_download[source_code_hash]}/{name}"
            p1 = subprocess.Popen(
                [
                    "ls",
                    "-ln",
                    filename,
                ],
                stdout=subprocess.PIPE,
            )
            p2 = subprocess.Popen(["awk", "{print $5}"], stdin=p1.stdout, stdout=subprocess.PIPE)
            p1.stdout.close()  # type: ignore
            # returns downloaded files size in bytes
            self.data_transfer_in_requested = byte_to_mb(p2.communicate()[0].decode("utf-8").strip())
            logging.info(
                f"data_transfer_in_requested={self.data_transfer_in_requested} MB |"
                f" Rounded={int(self.data_transfer_in_requested)} MB"
            )
        return True

    def remove_downloaded_file(self, source_code_hash, _id, pathname):
        if not self.is_already_cached[source_code_hash] and self.jobInfo[0]["storageDuration"][_id]:
            _remove(pathname)

    def get_data_init(self, key, _id, is_job_key=False):
        try:
            gdrive_info = subprocess_call(["gdrive", "info", "--bytes", key, "-c", env.GDRIVE_METADATA], 10)
        except Exception as e:
            raise e

        mime_type = gdrive.get_file_info(gdrive_info, _type="Mime")
        folder_name = gdrive.get_file_info(gdrive_info, _type="Name")

        logging.info(f"mime_type={mime_type}")
        if is_job_key:
            # key for the sourceCode tar.gz file is obtained
            try:
                self.data_transfer_in_to_download, self.job_key_list, key = gdrive.size(
                    key,
                    mime_type,
                    folder_name,
                    gdrive_info,
                    self.results_folder_prev,
                    self.source_code_hashes,
                    self.is_already_cached,
                )
            except Exception as e:
                raise e

        return mime_type, folder_name

    def get_data(self, key, _id, is_job_key=False):
        try:
            (
                mime_type,
                name,
            ) = self.get_data_init(key, _id, is_job_key)
        except Exception as e:
            print_tb(e)
            raise e

        if is_job_key:
            if self.data_transfer_in_to_download > self.data_transfer_in_requested:
                logging.error(
                    "E: requested size to download the sourceCode and datafiles is greater than the given amount"
                )
                # TODO: full refund
                raise

            try:
                cmd = ["gdrive", "info", "--bytes", key, "-c", env.GDRIVE_METADATA]
                gdrive_info = subprocess_call(cmd, 1)
            except Exception as e:
                # TODO: gdrive list --query "sharedWithMe"
                raise e

            mime_type = gdrive.get_file_info(gdrive_info, "Mime")
            name = gdrive.get_file_info(gdrive_info, "Name")

        # folder is already stored by its source_code_hash
        source_code_hash = name.replace(".tar.gz", "")
        logging.info(f"name={name}")
        logging.info(f"mime_type={mime_type}")
        if _id == 0:
            # source code folder, ignore downloading result-*
            name = f"{name}.tar.gz"
            try:
                output = gdrive.get_file_id(key)
            except Exception as e:
                print_tb()
                raise e

            key = echo_grep_awk(output, name, "1")
            mime_type = "gzip"

        if "gzip" in mime_type:
            try:
                cmd = ["gdrive", "info", "--bytes", key, "-c", env.GDRIVE_METADATA]
                gdrive_info = subprocess_call(cmd, 10)
            except Exception as e:
                print_tb()
                raise e

            source_code_hash = gdrive.get_file_info(gdrive_info, "Md5sum")
            self.md5sum_dict[key] = source_code_hash
            logging.info(f"md5sum={self.md5sum_dict[key]}")

            # recieved job is in folder tar.gz
            self.folder_type_dict[source_code_hash] = "gzip"
            try:
                self.cache(_id, name, source_code_hash, key, is_job_key)
            except Exception as e:
                raise e

            if is_job_key:
                target = self.results_folder
            else:
                target = f"{self.results_data_folder}/{source_code_hash}"
                mkdir(target)

            try:
                cache_folder = self.folder_path_to_download[source_code_hash]
                untar(f"{cache_folder}/{name}", target)
                return target
            except Exception as e:
                print_tb(e)
                raise e

            self.remove_downloaded_file(source_code_hash, _id, f"{cache_folder}/{name}")
        elif "folder" in mime_type:
            # Recieved job is in folder format
            self.folder_type_dict[source_code_hash] = "folder"
            try:
                self.cache(_id, name, source_code_hash, key, is_job_key)
            except Exception as e:
                raise e

            cache_folder = self.folder_path_to_download[source_code_hash]
            cmd = [
                "rsync",
                "-avq",
                "--partial-dir",
                "--omit-dir-times",
                f"{cache_folder}/{name}/",
                self.results_folder,
            ]
            try:
                output = run(cmd)
            except Exception as e:
                print_tb()
                raise e

            self.remove_downloaded_file(source_code_hash, _id, f"{cache_folder}/{name}/")
            tar_file = f"{self.results_folder}/{name}.tar.gz"
            try:
                untar(tar_file, self.results_folder)
                _remove(tar_file)
                return target
            except Exception as e:
                print_tb()
                raise e
        else:
            raise

    def run(self) -> bool:
        self.start_time = time.time()
        if env.IS_THREADING_ENABLED:
            self.thread_log_setup()

        log(f"{br(get_time())} job's source code has been sent through Google Drive", "cyan")
        if os.path.isdir(self.results_folder):
            self.get_data_init(key=self.job_key, _id=0, is_job_key=True)

        try:
            # Attempt to download the source code
            target = self.get_data(key=self.job_key, _id=0, is_job_key=True)
            if not os.path.isdir(f"{target}/.git"):
                log(f"Warning: .git folder does not exist within {target}")
                git.generate_git_repo(target)
        except:
            return False

        if not self.check_run_sh():
            self.complete_refund()

        for idx, (_, value) in enumerate(self.job_key_list.items()):
            try:
                target = self.get_data(value, idx + 1)
                if not os.path.isdir(f"{target}/.git"):
                    log(f"warning: .git folder does not exist within {target}")
                    git.generate_git_repo(target)
            except:
                return False

        return self.sbatch_call()
