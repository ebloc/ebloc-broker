#!/usr/bin/env python3
import json
import os
import subprocess

from config import logging
from lib import (GDRIVE_METADATA, convert_byte_to_mb, echo_grep_awk, execute_shell_command,
                 subprocess_call_attempt)


def gdrive_list(tar_hash, is_folder=False):
    if is_folder:
        result = (
            subprocess.check_output(["gdrive", "list", "--query", f"name='{tar_hash}'", "--no-header"])
            .decode("utf-8")
            .strip()
        )
    else:
        result = (
            subprocess.check_output(["gdrive", "list", "--query", f"name='{tar_hash}.tar.gz'", "--no-header"])
            .decode("utf-8")
            .strip()
        )
        #  result = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + tar_hash + '.tar.gz' + '\'', '--no-header']).decode('utf-8').strip()
    return result


def gdrive_upload_internal(dir_path, tar_hash, is_folder=False):
    if is_folder:
        subprocess.run(["gdrive", "upload", "--recursive", f"{dir_path}/{tar_hash}"])

        result = (
            subprocess.check_output(["gdrive", "list", "--query", f"name='{tar_hash}'", "--no-header"])
            .decode("utf-8")
            .strip()
        )
    else:
        # subprocess.run(['mv', folderToShare + '.tar.gz', tar_hash + '.tar.gz'])
        tar_file_path = f"{dir_path}/{tar_hash}.tar.gz"
        subprocess.run(["gdrive", "upload", tar_file_path])
        os.remove(tar_file_path)

        result = (
            subprocess.check_output(["gdrive", "list", "--query", f"name='{tar_hash}.tar.gz'", "--no-header"])
            .decode("utf-8")
            .strip()
        )
        # result = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + tar_hash + '.tar.gz' + '\'', '--no-header']).decode('utf-8').strip()

    return result.split(" ")[0]


def getMd5sum(gdrive_info):
    # cmd: echo gdrive_info | grep \'Mime\' | awk \'{print $2}\'
    return echo_grep_awk(gdrive_info, "Md5sum", "2")


def get_gdrive_file_info(gdrive_info, _type):
    # cmd: echo gdrive_info | grep _type | awk \'{print $2}\'
    return echo_grep_awk(gdrive_info, _type, "2")


def gdrive_get_file_id(key):
    command = ["gdrive", "list", "--query", "'" + key + "'" + " in parents"]
    status, result = execute_shell_command(command, None, True)
    return result


def gdrive_size(
    key, mimeType, folderName, gdrive_info, results_folder_prev, source_code_hash_list, shouldAlreadyCached
):
    source_code_key = None
    if "folder" in mimeType:
        job_key_list = []
        # rounded_size = 0
        size_to_download = 0

        result = gdrive_get_file_id(key)
        dataFiles_json_id = echo_grep_awk(result, "meta_data.json", "1")
        # key for the sourceCode elimination result*.tar.gz files
        source_code_key = echo_grep_awk(result, f"{folderName}.tar.gz", "1")

        status, res = subprocess_call_attempt(
            ["gdrive", "download", "--recursive", dataFiles_json_id, "--force", "--path", results_folder_prev], 10
        )
        if not status:
            return False

        status, gdrive_info = subprocess_call_attempt(
            ["gdrive", "info", "--bytes", source_code_key, "-c", GDRIVE_METADATA], 10
        )
        if not status:
            return False

        md5sum = get_gdrive_file_info(gdrive_info, "Md5sum")
        if md5sum != source_code_hash_list[0].decode("utf-8"):
            # Checks md5sum obtained from gdrive and given by the user
            logging.info("E: md5sum does not match with the provided data[0]")
            return False, 0, [], source_code_key

        byte_size = int(get_gdrive_file_info(gdrive_info, "Size"))
        logging.info(f"sourceCodeHash[0]_size={byte_size} bytes")
        if not shouldAlreadyCached[source_code_hash_list[0].decode("utf-8")]:
            size_to_download = byte_size

        logging.info(f"meta_data_path={results_folder_prev}/meta_data.json")
        with open(f"{results_folder_prev}/meta_data.json") as json_file:
            meta_data = json.load(json_file)

        for idx, (k, v) in enumerate(meta_data.items(), start=1):
            job_key_list.append(str(v))
            _key = str(v)
            status, gdrive_info = subprocess_call_attempt(
                ["gdrive", "info", "--bytes", _key, "-c", GDRIVE_METADATA], 10
            )
            if not status:
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
            if not shouldAlreadyCached[source_code_hash_list[idx].decode("utf-8")]:
                size_to_download += _size

        ret_size = int(convert_byte_to_mb(size_to_download))
        logging.info(f"Total_size={byte_size} bytes | Size to download={size_to_download} bytes ==> {ret_size} MB")
        return True, ret_size, job_key_list, source_code_key
    else:
        return False, 0, [], source_code_key

    """
    elif 'gzip' in mimeType:
        byte_size = lib.get_gdrive_file_info(gdrive_info, 'Size')
        rounded_size = int(convert_byte_to_mb(byte_size))
    """
