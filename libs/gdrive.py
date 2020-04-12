#!/usr/bin/env python3

import json
import os
import subprocess

from config import bp, logging  # noqa: F401
from lib import echo_grep_awk, run_command, subprocess_call
from settings import init_env
from utils import _colorize_traceback, byte_to_mb, read_json

env = init_env()


def list(tar_hash, is_folder=False):
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


def upload_internal(dir_path, tar_hash, is_folder=False):
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


def get_file_info(gdrive_info, _type):
    return echo_grep_awk(gdrive_info, _type, "2")


def get_file_id(key):
    cmd = ["gdrive", "list", "--query", f"'{key}' in parents"]
    success, output = run_command(cmd, None, True)
    return output


def get_data_key_ids(results_folder_prev):
    f = f"{results_folder_prev}/meta_data.json"
    logging.info(f"meta_data_path={f}")
    try:
        meta_data = read_json(f)
    except:
        logging.error(_colorize_traceback())
        return False, ""

    return True, meta_data


def size(
    key, mime_type, folder_name, gdrive_info, results_folder_prev, source_code_hash_list, is_cached,
):
    source_code_key = None
    size_to_download = 0
    if "folder" in mime_type:
        output = get_file_id(key)
        data_files_id = echo_grep_awk(output, "meta_data.json", "1")
        # key for the sourceCode elimination output*.tar.gz files
        source_code_key = echo_grep_awk(output, f"{folder_name}.tar.gz", "1")
        try:
            if not data_files_id:
                return False

            cmd = [
                "gdrive",
                "download",
                "--recursive",
                data_files_id,
                "--force",
                "--path",
                results_folder_prev,
            ]
            output = subprocess_call(cmd, 10)

            cmd = [
                "gdrive",
                "info",
                "--bytes",
                source_code_key,
                "-c",
                env.GDRIVE_METADATA,
            ]
            gdrive_info = subprocess_call(cmd, 10)
        except:
            return False

        md5sum = get_file_info(gdrive_info, "Md5sum")
        if md5sum != source_code_hash_list[0].decode("utf-8"):
            # checks md5sum obtained from gdrive and given by the user
            logging.error("E: md5sum does not match with the provided data[0]")
            return False, 0, [], source_code_key
        else:
            logging.info(f"Success on {md5sum} folder")

        byte_size = int(get_file_info(gdrive_info, "Size"))
        logging.info(f"sourceCodeHash[0]_size={byte_size} bytes")
        if not is_cached[source_code_hash_list[0].decode("utf-8")]:
            size_to_download += byte_size

        success, meta_data = get_data_key_ids(results_folder_prev)
        if not success:
            return False

        data_key_dict = {}
        for idx, (k, v) in enumerate(meta_data.items(), start=1):
            _key = str(v)
            output = get_file_id(_key)
            data_key = echo_grep_awk(output, f"{k}.tar.gz", "1")
            try:
                cmd = ["gdrive", "info", "--bytes", data_key, "-c", env.GDRIVE_METADATA]
                gdrive_info = subprocess_call(cmd, 10)
            except:
                return False

            md5sum = get_file_info(gdrive_info, "Md5sum")
            if md5sum != source_code_hash_list[idx].decode("utf-8"):
                # checks md5sum obtained from gdrive and given by the user
                logging.error(
                    f"md5sum={md5sum} | given={source_code_hash_list[idx].decode('utf-8')} \n"
                    f"E: md5sum does not match with the provided data[{idx}]"
                )
                return False, 0, [], source_code_key

            data_key_dict[md5sum] = data_key
            _size = int(get_file_info(gdrive_info, "Size"))
            logging.info(f"sourceCodeHash[{idx}]_size={_size} bytes")
            byte_size += _size
            if not is_cached[source_code_hash_list[idx].decode("utf-8")]:
                size_to_download += _size

        data_link_file = f"{results_folder_prev}/meta_data_link.json"
        if bool(data_key_dict):
            with open(data_link_file, "w") as f:
                json.dump(data_key_dict, f)
        else:
            logging.error("E: Something is wrong. data_key_dict is {}.")
            return False, 0, [], source_code_key

        output = byte_to_mb(size_to_download)
        logging.info(f"Total_size={byte_size} bytes | Size to download={size_to_download} bytes => {output} MB")
        return True, output, data_key_dict, source_code_key
    else:
        return False, 0, [], source_code_key
