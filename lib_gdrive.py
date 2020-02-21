#!/usr/bin/env python3
import os
import subprocess


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
