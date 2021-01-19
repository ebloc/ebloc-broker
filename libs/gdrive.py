#!/usr/bin/env python3

import json
import subprocess

# import gshell
from config import env, logging
from lib import echo_grep_awk, run, subprocess_call
from utils import _colorize_traceback, byte_to_mb, log, read_json, silent_remove

# TODO: gdrive list --query "sharedWithMe"


def _list(tar_hash, is_folder=False):
    if is_folder:
        filename = f"name='{tar_hash}'"
    else:
        filename = f"name='{tar_hash}.tar.gz'"

    # run(['gdrive', 'list', '--query', 'name contains \'' + tar_hash + '.tar.gz' + '\'', '--no-header'])
    return run(["gdrive", "list", "--query", filename, "--no-header",])


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
        silent_remove(tar_file_path)
        output = (
            subprocess.check_output(["gdrive", "list", "--query", f"name='{file_name_to_upload}'", "--no-header",])
            .decode("utf-8")
            .strip()
        )
        # output = subprocess.check_output(['gdrive', 'list', '--query', 'name contains \'' + tar_hash + '.tar.gz' + '\'', '--no-header']).decode('utf-8').strip()
    return output.split(" ")[0]


def get_file_info(gdrive_info, _type):
    return echo_grep_awk(gdrive_info, _type, "2")


def get_file_id(key):
    return run(["gdrive", "list", "--query", f"'{key}' in parents"])


def get_data_key_ids(results_folder_prev):
    filename = f"{results_folder_prev}/meta_data.json"
    log(f"==> meta_data_path={filename}")
    try:
        meta_data = read_json(filename)
    except:
        _colorize_traceback()
        return False, ""

    return True, meta_data


def size(key, mime_type, folder_name, gdrive_info, results_folder_prev, source_code_hashes, is_cached):
    source_code_key = None
    size_to_download = 0
    if "folder" in mime_type:
        try:
            output = get_file_id(key)
        except:
            return False

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
        except:
            # TODO: gdrive list --query "sharedWithMe"
            return False

        md5sum = get_file_info(gdrive_info, "Md5sum")
        if md5sum != source_code_hashes[0].decode("utf-8"):
            # checks md5sum obtained from gdrive and given by the user
            logging.error(f"E: md5sum does not match with the provided data {source_code_key}")
            _colorize_traceback()
            return False, 0, [], source_code_key
        else:
            logging.info(f"SUCCESS on {md5sum} folder")

        byte_size = int(get_file_info(gdrive_info, "Size"))
        logging.info(f"source_code_hash[0]_size={byte_size} bytes")
        if not is_cached[source_code_hashes[0].decode("utf-8")]:
            size_to_download += byte_size

        success, meta_data = get_data_key_ids(results_folder_prev)
        if not success:
            return False

        data_key_dict = {}
        for idx, (k, v) in enumerate(meta_data.items(), start=1):
            _key = str(v)
            try:
                output = get_file_id(_key)
                data_key = echo_grep_awk(output, f"{k}.tar.gz", "1")
                cmd = ["gdrive", "info", "--bytes", data_key, "-c", env.GDRIVE_METADATA]
                gdrive_info = subprocess_call(cmd, 10)
            except:
                return False

            md5sum = get_file_info(gdrive_info, _type="Md5sum")
            log(gdrive_info, color="yellow")
            given_source_code_hash = source_code_hashes[idx].decode("utf-8")
            log(f"==> given_source_code_hash={given_source_code_hash}  idx={idx}")
            if md5sum != given_source_code_hash:
                # checks md5sum obtained from gdrive and given by the user
                logging.error(
                    f"\nE: md5sum does not match with the provided data[{idx}]\n"
                    f"md5sum={md5sum} <==> given={given_source_code_hash} \n"
                )
                return False, 0, [], source_code_key

            data_key_dict[md5sum] = data_key
            _size = int(get_file_info(gdrive_info, "Size"))
            logging.info(f"source_code_hash[{idx}]_size={_size} bytes")
            byte_size += _size
            if not is_cached[source_code_hashes[idx].decode("utf-8")]:
                size_to_download += _size

        data_link_file = f"{results_folder_prev}/meta_data_link.json"
        if bool(data_key_dict):
            with open(data_link_file, "w") as f:
                json.dump(data_key_dict, f)
        else:
            logging.error("E: Something is wrong. data_key_dict is {}")
            return False, 0, [], source_code_key

        output = byte_to_mb(size_to_download)
        logging.info(f"Total_size={byte_size} bytes | size to download={size_to_download} bytes => {output} MB")
        return True, output, data_key_dict, source_code_key
    else:
        return False, 0, [], source_code_key
