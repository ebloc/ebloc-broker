#!/usr/bin/env python3

import json
import os
import shutil
import subprocess
import sys

from broker._utils._log import br
from broker._utils.tools import mkdir
from broker.config import env, logging
from broker.errors import QuietExit
from broker.lib import echo_grep_awk, run, subprocess_call
from broker.utils import _remove, byte_to_mb, compress_folder, dump_dict_to_file, log, print_tb, read_json

# TODO: gdrive list --query "sharedWithMe"


def check_user(_user):
    output = run(["gdrive", "about"])
    user = output.partition("\n")[0].split(", ")[1]
    return user == _user, user


def submit(provider, _from, job):
    try:
        job.check_account_status(_from)
        job.Ebb.is_provider_valid(provider)
        job.Ebb.is_requester_valid(_from)
    except Exception as e:
        raise e

    try:
        provider_info = job.Ebb.get_provider_info(provider)
        log(f"==> Provider's available_core_num={provider_info['available_core_num']}")
        log(f"==> Provider's price_core_min={provider_info['price_core_min']}")
    except Exception as e:
        raise QuietExit from e

    provider = job.Ebb.w3.toChecksumAddress(provider)
    provider_to_share = provider_info["email"]
    try:
        if len(job.folders_to_share) > 1:
            for folder_to_share in job.folders_to_share[1:]:
                # starting from the first element ignoring source_folder
                # attempting to share the data folder
                job_key, tar_hash, job.tar_hashes = share_folder(folder_to_share, provider_to_share, job.base_dir)
                job.foldername_tar_hash[folder_to_share] = tar_hash
                job.keys[tar_hash] = job_key

            if job.base_dir == "":
                print_tb("job.base_dir is empty")
                sys.exit()

            data_files_json_path = f"{job.base_dir}/meta_data.json"  #
            try:
                data_json = read_json(data_files_json_path)
                if job.keys == data_json:
                    log("#> meta_data.json file matches with the given data keys", "bold green")
                else:
                    log("#> meta_data.json file does not match with the given data keys", "bold blue")
                    _dump_dict_to_file(data_files_json_path, job.keys)
                    data_json = read_json(data_files_json_path)
            except:
                _dump_dict_to_file(data_files_json_path, job.keys)
                data_json = read_json(data_files_json_path)

            log("meta_data-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-", "blue")
            log(data_json)
            log("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-", "blue")

        folder_to_share = job.folders_to_share[0]
        job_key, tar_hash, job.tar_hashes = share_folder(
            folder_to_share, provider_to_share, job.base_dir, job_key_flag=True
        )
        job.foldername_tar_hash[folder_to_share] = tar_hash
        job.keys[tar_hash] = job_key
        return job
    except Exception as e:
        print_tb()
        raise e


def share_folder(folder_to_share, provider_to_share, base_dir, job_key_flag=False):
    logging.info(f"folder_to_share={folder_to_share}")
    key, is_already_uploaded, tar_hash, tar_hashes = upload(folder_to_share, base_dir, job_key_flag)
    cmd = ["gdrive", "share", key, "--role", "writer", "--type", "user", "--email", provider_to_share]
    if not is_already_uploaded:
        log(f"share_output={run(cmd)}")

    return key, tar_hash, tar_hashes


def upload(folder_to_share, base_dir, job_key_flag=False):
    tar_hashes = {}
    is_already_uploaded = False
    log(f"==> job_key_flag={job_key_flag}, tar.gz file is inside the base folder")
    dir_path = os.path.dirname(folder_to_share)
    tar_hash, _ = compress_folder(folder_to_share, is_exclude_git=True)
    tar_hashes[folder_to_share] = tar_hash

    path_to_move = f"{dir_path}/{tar_hash}"
    _from = f"{dir_path}/{tar_hash}.tar.gz"
    _to = f"{path_to_move}/{tar_hash}.tar.gz"

    mkdir(path_to_move)
    shutil.move(_from, _to)
    if job_key_flag:
        shutil.copyfile(f"{base_dir}/meta_data.json", f"{path_to_move}/meta_data.json")

    is_file_exist = _list(tar_hash, is_folder=True)
    if not is_file_exist:
        key = _upload(dir_path, tar_hash, is_folder=True)
        log(f"{_list(tar_hash)}", "green")
    else:
        log(f"==> Requested folder {tar_hash} is already uploaded", "blue")
        log(is_file_exist, "green")
        key = is_file_exist.partition("\n")[0].split()[0]
        is_already_uploaded = True

    _remove(f"{dir_path}/{tar_hash}")  # created .tar.gz file is removed
    return key, is_already_uploaded, tar_hash, tar_hashes


def _list(tar_hash, is_folder=False):
    if is_folder:
        filename = f"name='{tar_hash}'"
    else:
        filename = f"name='{tar_hash}.tar.gz'"

    # run(['gdrive', 'list', '--query', 'name contains \'' + tar_hash + '.tar.gz' + '\'', '--no-header'])
    return run(
        [
            "gdrive",
            "list",
            "--query",
            filename,
            "--no-header",
        ]
    )


def _upload(dir_path, tar_hash, is_folder=False):
    if is_folder:
        subprocess.run(["gdrive", "upload", "--recursive", f"{dir_path}/{tar_hash}"], check=True)
        output = (
            subprocess.check_output(["gdrive", "list", "--query", f"name='{tar_hash}'", "--no-header"])
            .decode("utf-8")
            .strip()
        )
    else:
        # subprocess.run(['mv', folderToShare + '.tar.gz', tar_hash + '.tar.gz'])
        file_name_to_upload = f"{tar_hash}.tar.gz"
        tar_file_path = f"{dir_path}/{file_name_to_upload}"
        subprocess.run(["gdrive", "upload", tar_file_path], check=True)
        _remove(tar_file_path)
        output = (
            subprocess.check_output(
                [
                    "gdrive",
                    "list",
                    "--query",
                    f"name='{file_name_to_upload}'",
                    "--no-header",
                ]
            )
            .decode("utf-8")
            .strip()
        )
        # cmd = ['gdrive', 'list', '--query', 'name contains \'' + tar_hash + '.tar.gz' + '\'', '--no-header']
        # output = subprocess.check_output(cmd).decode('utf-8').strip()
    return output.split(" ")[0]


def get_file_info(gdrive_info, _type):
    return echo_grep_awk(gdrive_info, _type, "2")


def get_file_id(key):
    return run(["gdrive", "list", "--query", f"'{key}' in parents"])


def get_data_key_ids(results_folder_prev) -> bool:
    filename = f"{results_folder_prev}/meta_data.json"
    log(f"==> meta_data_path={filename}")
    try:
        meta_data = read_json(filename)
    except Exception as e:
        print_tb(e)

    return meta_data


def size(key, mime_type, folder_name, gdrive_info, results_folder_prev, source_code_hashes, is_cached):
    source_code_key = None
    size_to_download = 0
    if "folder" in mime_type:
        try:
            output = get_file_id(key)
            log(f"==> data_id={key}")
            log(output, "bold green")
        except Exception as e:
            raise e

        data_files_id = echo_grep_awk(output, "meta_data.json", "1")
        # key for the sourceCode elimination output*.tar.gz files
        source_code_key = echo_grep_awk(output, f"{folder_name}.tar.gz", "1")
        try:
            if not data_files_id:
                raise

            cmd = [
                "gdrive",
                "download",
                "--recursive",
                data_files_id,  # first id is meta_data
                "--force",
                "--path",
                results_folder_prev,
            ]
            output = subprocess_call(cmd, 10)
            print(output)
            cmd = [
                "gdrive",
                "info",
                "--bytes",
                source_code_key,
                "-c",
                env.GDRIVE_METADATA,
            ]
            gdrive_info = subprocess_call(cmd, 10)
        except Exception as e:
            # TODO: gdrive list --query "sharedWithMe"
            raise e

        md5sum = get_file_info(gdrive_info, "Md5sum")
        _source_code_hash = source_code_hashes[0].decode("utf-8")
        if md5sum != _source_code_hash:
            # checks md5sum obtained from gdrive and given by the user
            print_tb(f"E: md5sum does not match with the provided data {source_code_key}")
            raise

        log(f"SUCCESS on {md5sum} folder", "bold green")
        byte_size = int(get_file_info(gdrive_info, "Size"))
        log(f"==> source_code_hashes[0] == {_source_code_hash} size={byte_size} bytes")
        if not is_cached[source_code_hashes[0].decode("utf-8")]:
            size_to_download += byte_size

        try:
            meta_data = get_data_key_ids(results_folder_prev)
        except Exception as e:
            raise e

        data_key_dict = {}
        for idx, (k, v) in enumerate(meta_data.items(), start=1):
            _key = str(v)
            try:
                output = get_file_id(_key)
                data_key = echo_grep_awk(output, f"{k}.tar.gz", "1")
                cmd = ["gdrive", "info", "--bytes", data_key, "-c", env.GDRIVE_METADATA]
                gdrive_info = subprocess_call(cmd, 10)
            except Exception as e:
                raise e

            md5sum = get_file_info(gdrive_info, _type="Md5sum")
            log(gdrive_info, "yellow")
            given_source_code_hash = source_code_hashes[idx].decode("utf-8")
            log(f"==> given_source_code_hash={given_source_code_hash}  idx={idx}")
            if md5sum != given_source_code_hash:
                # checks md5sum obtained from gdrive and given by the user
                raise Exception(
                    f"\nE: md5sum does not match with the provided data{br(idx)}\n"
                    f"md5sum={md5sum} | given={given_source_code_hash}"
                )

            data_key_dict[md5sum] = data_key
            _size = int(get_file_info(gdrive_info, "Size"))
            log(f"==> source_code_hashes{br(idx)} == {source_code_hashes[idx].decode('utf-8')} size={_size} bytes")
            byte_size += _size
            if not is_cached[source_code_hashes[idx].decode("utf-8")]:
                size_to_download += _size

        data_link_file = f"{results_folder_prev}/meta_data_link.json"
        if bool(data_key_dict):
            with open(data_link_file, "w") as f:
                json.dump(data_key_dict, f)
        else:
            raise Exception("E: Something is wrong. data_key_dict is empty")

        output = byte_to_mb(size_to_download)
        logging.info(f"Total_size={byte_size} bytes | size to download={size_to_download} bytes => {output} MB")
        return output, data_key_dict, source_code_key
    else:
        raise


def _dump_dict_to_file(filename, job_keys):
    try:
        dump_dict_to_file(filename, job_keys)
        log("==> meta_data.json file is updated into the parent folder")
    except Exception as e:
        print_tb()
        raise e
