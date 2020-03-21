#!/usr/bin/env python3
import json
import os
import subprocess

from config import logging
from lib import (GDRIVE_METADATA, echo_grep_awk, run_command,
                 subprocess_call_attempt)
from utils import byte_to_mb, read_json


def gdrive_list(tar_hash, is_folder=False):
    if is_folder:
        output = (
            subprocess.check_output(["gdrive", "list", "--query", f"name='{tar_hash}'", "--no-header"])
            .decode("utf-8")
            .strip()
        )
    else:
        output = (
            subprocess.check_output(["gdrive", "list", "--query", f"name='{tar_hash}.tar.gz'", "--no-header",])
            .decode("utf-8")
            .strip()
        )
        #  output = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + tar_hash + '.tar.gz' + '\'', '--no-header']).decode('utf-8').strip()
    return output


def gdrive_upload_internal(dir_path, tar_hash, is_folder=False):
    if is_folder:
        subprocess.run(["gdrive", "upload", "--recursive", f"{dir_path}/{tar_hash}"])

        output = (
            subprocess.check_output(["gdrive", "list", "--query", f"name='{tar_hash}'", "--no-header"])
            .decode("utf-8")
            .strip()
        )
    else:
        # subprocess.run(['mv', folderToShare + '.tar.gz', tar_hash + '.tar.gz'])
        tar_file_path = f"{dir_path}/{tar_hash}.tar.gz"
        subprocess.run(["gdrive", "upload", tar_file_path])
        os.remove(tar_file_path)

        output = (
            subprocess.check_output(["gdrive", "list", "--query", f"name='{tar_hash}.tar.gz'", "--no-header",])
            .decode("utf-8")
            .strip()
        )
        # output = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + tar_hash + '.tar.gz' + '\'', '--no-header']).decode('utf-8').strip()
    return output.split(" ")[0]


def getMd5sum(gdrive_info):
    # cmd: echo gdrive_info | grep \'Mime\' | awk \'{print $2}\'
    return echo_grep_awk(gdrive_info, "Md5sum", "2")


def get_gdrive_file_info(gdrive_info, _type):
    # cmd: echo gdrive_info | grep _type | awk \'{print $2}\'
    return echo_grep_awk(gdrive_info, _type, "2")


def gdrive_get_file_id(key):
    cmd = ["gdrive", "list", "--query", "'" + key + "'" + " in parents"]
    success, output = run_command(cmd, None, True)
    return output


def gdrive_size(
    key, mime_type, folder_name, gdrive_info, results_folder_prev, source_code_hash_list, is_cached,
):
    source_code_key = None
    if "folder" in mime_type:
        job_key_list = []
        # rounded_size = 0
        size_to_download = 0

        output = gdrive_get_file_id(key)
        dataFiles_json_id = echo_grep_awk(output, "meta_data.json", "1")
        # key for the sourceCode elimination output*.tar.gz files
        source_code_key = echo_grep_awk(output, f"{folder_name}.tar.gz", "1")

        success, output = subprocess_call_attempt(
            ["gdrive", "download", "--recursive", dataFiles_json_id, "--force", "--path", results_folder_prev,], 10,
        )
        if not success:
            return False

        success, gdrive_info = subprocess_call_attempt(
            ["gdrive", "info", "--bytes", source_code_key, "-c", GDRIVE_METADATA], 10
        )
        if not success:
            return False

        md5sum = get_gdrive_file_info(gdrive_info, "Md5sum")
        if md5sum != source_code_hash_list[0].decode("utf-8"):
            # Checks md5sum obtained from gdrive and given by the user
            logging.info("E: md5sum does not match with the provided data[0]")
            return False, 0, [], source_code_key

        byte_size = int(get_gdrive_file_info(gdrive_info, "Size"))
        logging.info(f"sourceCodeHash[0]_size={byte_size} bytes")
        if not is_cached[source_code_hash_list[0].decode("utf-8")]:
            size_to_download = byte_size

        f = f"{results_folder_prev}/meta_data.json"
        logging.info(f"meta_data_path={f}")
        success, meta_data = read_json(f)
        if not success:
            return False

        for idx, (k, v) in enumerate(meta_data.items(), start=1):
            job_key_list.append(str(v))
            _key = str(v)
            success, gdrive_info = subprocess_call_attempt(
                ["gdrive", "info", "--bytes", _key, "-c", GDRIVE_METADATA], 10
            )
            if not success:
                return False

            md5sum = get_gdrive_file_info(gdrive_info, "Md5sum")
            if md5sum != source_code_hash_list[idx].decode("utf-8"):
                # Checks md5sum obtained from gdrive and given by the user
                print(idx)
                logging.error(
                    f"md5sum={md5sum} | given={source_code_hash_list[idx].decode('utf-8')} \n"
                    f"E: md5sum does not match with the provided data[{idx}]"
                )
                return False, 0, [], source_code_key

            _size = int(get_gdrive_file_info(gdrive_info, "Size"))
            logging.info(f"sourceCodeHash[{idx}]_size={_size} bytes")
            byte_size += _size
            if not is_cached[source_code_hash_list[idx].decode("utf-8")]:
                size_to_download += _size

        output = byte_to_mb(size_to_download)
        logging.info(f"Total_size={byte_size} bytes | Size to download={size_to_download} bytes ==> {output} MB")
        return True, output, job_key_list, source_code_key
    else:
        return False, 0, [], source_code_key

    """
    elif 'gzip' in mime_type:
        byte_size = lib.get_gdrive_file_info(gdrive_info, 'Size')
        rounded_size = byte_to_mb(byte_size)
    """
