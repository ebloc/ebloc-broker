#!/usr/bin/env python3

import json
import os
import shutil
import subprocess
import sys
from contextlib import suppress
from pathlib import Path

from broker._utils._log import br, ok
from broker._utils.tools import _remove, mkdir, read_json
from broker.config import env
from broker.lib import echo_grep_awk, run, subprocess_call
from broker.utils import byte_to_mb, compress_folder, dump_dict_to_file, is_program_valid, log, print_tb


def check_gdrive():
    """Check whether `gdrive about` returns a valid output."""
    is_program_valid(["gdrive", "version"])
    try:
        output = run(["gdrive", "about"])
    except:
        with open(Path.home() / ".gdrive" / "token_v2.json", "r") as f:
            output = json.load(f)

        log("#> Trying: gdrive about --refresh-token <id>")
        run(["gdrive", "about", "--refresh-token", output["refresh_token"]])
        output = run(["gdrive", "about"])  # re-try

    return output


def check_gdrive_about(given_user):
    output = check_gdrive()
    user = output.partition("\n")[0].split(", ")[1]
    return user == given_user, user


def submit(_from, job):
    try:
        job.check_account_status(_from)
        # job.Ebb.is_provider_valid(provider)
        job.Ebb.is_requester_valid(_from)
    except Exception as e:
        raise e

    folder_ids_to_share = []
    data_files_json_path = f"{job.tmp_dir}/meta_data.json"
    try:
        if len(job.folders_to_share) > 1:
            for folder_to_share in job.folders_to_share[1:]:
                if not isinstance(folder_to_share, bytes):
                    # starting from the first data file ignoring source_folder
                    # attempting to share the data folder
                    folder_key, tar_hash, job.tar_hashes = upload_folder(folder_to_share, job.tmp_dir)
                    folder_ids_to_share.append(folder_key)  # record keys to share at end
                    job.foldername_tar_hash[folder_to_share] = tar_hash
                    job.keys[tar_hash] = folder_key

            if job.tmp_dir == "":
                print_tb("job.tmp_dir is empty")
                sys.exit()

            _dump_dict_to_file(data_files_json_path, job.keys)
            data_json = read_json(data_files_json_path)
            if data_json:
                log("## meta_data:")
                log(data_json)

            with suppress(Exception):
                data_json = read_json(data_files_json_path)
                if job.keys == data_json:
                    log(f"## meta_data.json file matches with the given data keys {ok()}")
                else:
                    log("warning: meta_data.json file does not match with the given data keys")

        folder_to_share = job.folders_to_share[0]
        if not isinstance(folder_to_share, bytes):
            folder_key, tar_hash, job.tar_hashes = upload_folder(folder_to_share, job.tmp_dir, folder_key_flag=True)
            folder_ids_to_share.append(folder_key)  # record keys to share at end
            job.foldername_tar_hash[folder_to_share] = tar_hash
            # add an element to the beginning of the dict since Python
            # 3.7. dictionaries are now ordered by insertion order.
            job.keys_final[tar_hash] = folder_key
            job.keys_final.update(job.keys)
            job.keys = job.keys_final

        return job, folder_ids_to_share
    except Exception as e:
        print_tb(e)
        raise e
    finally:
        _dump_dict_to_file(data_files_json_path, job.keys)
        data_json = read_json(data_files_json_path)
        if data_json:
            log("## meta_data:")
            log(data_json)

        _id = None
        for *_, v in data_json.items():
            _id = v
            break

        if _id:
            log("## updating meta_data ", end="")
            update_meta_data_gdrive(_id, data_files_json_path)
            log(ok())


def upload_folder(folder_to_share, tmp_dir, folder_key_flag=False):
    log(f"## folder_to_share={folder_to_share}")
    key, *_, tar_hash, tar_hashes = upload(folder_to_share, tmp_dir, folder_key_flag)
    return key, tar_hash, tar_hashes


def upload(folder_to_share, tmp_dir, is_source_code=False):
    tar_hashes = {}
    is_already_uploaded = False
    log(f"==> is_source_code={is_source_code} | tar.gz file is inside the base folder")
    dir_path = os.path.dirname(folder_to_share)
    tar_hash, _ = compress_folder(folder_to_share, is_exclude_git=True)
    tar_hashes[folder_to_share] = tar_hash
    path_to_move = f"{dir_path}/{tar_hash}"
    _from = f"{dir_path}/{tar_hash}.tar.gz"
    _to = f"{path_to_move}/{tar_hash}.tar.gz"
    mkdir(path_to_move)
    shutil.move(_from, _to)
    if is_source_code:
        shutil.copyfile(f"{tmp_dir}/meta_data.json", f"{path_to_move}/meta_data.json")

    is_file_exist = _list(tar_hash, is_folder=True)
    if is_file_exist:
        log(f"## requested folder {tar_hash} is already uploaded", "bold blue")
        log(is_file_exist, "bg")
        key = is_file_exist.partition("\n")[0].split()[0]
        is_already_uploaded = True
    else:
        key = _upload(dir_path, tar_hash, is_folder=True)
        log(f"{_list(tar_hash)}", "bg")

    _remove(f"{dir_path}/{tar_hash}")  # created .tar.gz file is removed
    return key, is_already_uploaded, tar_hash, tar_hashes


def delete_all(_type="all"):
    """Delete all created files and folder within the gdrive."""
    if _type == "dir":
        for line in list_all("dir").splitlines():
            try:
                run(["gdrive", "delete", "--recursive", line.split()[0]])
            except:
                pass
    else:
        for line in list_all().splitlines():
            if " dir   " not in line:  # first remove files
                try:
                    run(["gdrive", "delete", line.split()[0]])
                except Exception as e:
                    log(f"E {e}")

        for line in list_all().splitlines():
            if " dir   " in line:
                try:
                    log(f"Attempt to delete dir: {line.split()[0]} ", end="", h=False)
                    output = run(["/usr/local/bin/gdrive", "delete", "--recursive", line.split()[0]])
                    print(output)
                except Exception as e:
                    log(f"E {e}")
            # else:
            #     with suppress(Exception):
            #         run(["gdrive", "delete", line.split()[0]])


def list_all(_type="all"):
    if _type == "dir":
        _lines = ""
        lines = run(["gdrive", "list", "--no-header"])
        for line in lines.splitlines():
            if " dir   " in line:
                _lines += f"{line}\n"
                # breakpoint()  # DEBUG
        return _lines[:-1]
    else:
        lines = run(["gdrive", "list", "--no-header"])

    return lines


def _list(tar_hash, is_folder=False):
    r"""Query list from gdrive.

     cmd: run(['gdrive', 'list', '--query', 'name contains \'' + tar_hash + '.tar.gz' + '\'', '--no-header'])
    __https://developers.google.com/drive/api/v3/reference/query-ref
    """
    if is_folder:
        fn = f"name='{tar_hash}'"
    else:
        fn = f"name='{tar_hash}.tar.gz'"

    return run(
        [
            "gdrive",
            "list",
            "--query",
            f"{fn} and trashed=false",
            "--no-header",
        ]
    )


def _upload(dir_path, tar_hash, is_folder=False):
    if is_folder:
        subprocess.run(["gdrive", "upload", "--recursive", f"{dir_path}/{tar_hash}"], check=True)
        output = (
            subprocess.check_output(
                ["gdrive", "list", "--query", f"name='{tar_hash}' and trashed=false", "--no-header"]
            )
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
                    f"name='{file_name_to_upload}' and trashed=false",
                    "--no-header",
                ]
            )
            .decode("utf-8")
            .strip()
        )
        # cmd = ['gdrive', 'list', '--query', 'name contains \'' + tar_hash + '.tar.gz' + '\'', '--no-header']
        # output = subprocess.check_output(cmd).decode('utf-8').strip()
    return output.split(" ", maxsplit=1)[0]


def get_file_info(gdrive_info, _type):
    return echo_grep_awk(gdrive_info, _type, "2")


def get_file_id(key):
    return run(["gdrive", "list", "--query", f"'{key}' in parents and trashed=false"])


def get_data_key_ids(results_folder_prev) -> bool:
    fn = f"{results_folder_prev}/meta_data.json"
    log(f"==> meta_data_path={fn}")
    try:
        meta_data = read_json(fn)
    except Exception as e:
        print_tb(e)

    return meta_data


def update_meta_data_gdrive(key, path):
    output = get_file_id(key)
    meta_data_key = fetch_grive_output(output, "meta_data.json")
    log(f"\n\t`gdrive update {meta_data_key} {path}`", h=False, end="")
    run(["gdrive", "update", meta_data_key, path])


def fetch_grive_output(output, key):
    for line in output.split("\n"):
        if key in line:
            return line.split(" ")[0]

    raise Exception(f"gdrive: given key={key} does not exist")


def parse_gdrive_info(gdrive_info):
    try:
        _dict = {}
        for line in gdrive_info.splitlines():
            line = line.replace(" ", "")
            output = line.split(":")
            if output[0] not in ["DownloadUrl", "ViewUrl"]:
                _dict[output[0]] = output[1]

        log(_dict)
    except:
        log(gdrive_info, "bold yellow")


def size(key, mime_type, folder_name, gdrive_info, results_folder_prev, code_hashes, is_cached):
    source_code_key = None
    size_to_download = 0
    if "folder" not in mime_type:
        raise Exception

    try:
        output = get_file_id(key)
        log(f"==> data_id=[m]{key}")
        log(output, "bg")
        data_files_id = fetch_grive_output(output, "meta_data.json")
        if not data_files_id:
            raise Exception

        # key for the source_code elimination output*.tar.gz files
        source_code_key = fetch_grive_output(output, f"{folder_name}.tar.gz")
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
        print_tb(e)
        # TODO: gdrive list --query "sharedWithMe"
        raise e

    md5sum = get_file_info(gdrive_info, "Md5sum")
    _source_code_hash = code_hashes[0].decode("utf-8")
    if md5sum != _source_code_hash:
        # checks md5sum obtained from gdrive and given by the user
        raise Exception(f"md5sum does not match with the provided data {source_code_key}")

    log(f"SUCCESS on folder={md5sum}", "bg")
    byte_size = int(get_file_info(gdrive_info, "Size"))
    log(f"## code_hashes[0] == {_source_code_hash} | size={byte_size} bytes")
    if not is_cached[code_hashes[0].decode("utf-8")]:
        size_to_download += byte_size

    try:
        meta_data = get_data_key_ids(results_folder_prev)
    except Exception as e:
        raise e

    data_key_dict = {}
    if len(meta_data.items()) > 1:
        idx = 0
        for k, v in meta_data.items():
            if idx == 0:  # first item is for the source-code itself
                _key = str(v)
                output = get_file_id(_key)
                data_key = fetch_grive_output(output, f"{k}.tar.gz")
                cmd = ["gdrive", "info", "--bytes", data_key, "-c", env.GDRIVE_METADATA]
                gdrive_info = subprocess_call(cmd, 10)
                log(f" * gdrive_info for [g]{k}[/g]:")
                parse_gdrive_info(gdrive_info)
                idx += 1
            else:  # should start from the first index
                try:
                    _key = str(v)
                    output = get_file_id(_key)
                    data_key = fetch_grive_output(output, f"{k}.tar.gz")
                    cmd = ["gdrive", "info", "--bytes", data_key, "-c", env.GDRIVE_METADATA]
                    gdrive_info = subprocess_call(cmd, 10)
                except Exception as e:
                    raise e

                md5sum = get_file_info(gdrive_info, _type="Md5sum")
                log(f" * gdrive_info for [g]{k}[/g]:")
                parse_gdrive_info(gdrive_info)
                given_code_hash = code_hashes[idx].decode("utf-8")
                log(f"==> given_code_hash={given_code_hash}  idx={idx}")
                if md5sum != given_code_hash:
                    # checks md5sum obtained from gdrive and given by the user
                    raise Exception(
                        f"md5sum does not match with the provided data{br(idx)}\n"
                        f"md5sum={md5sum} | given={given_code_hash}"
                    )

                data_key_dict[md5sum] = data_key
                _size = int(get_file_info(gdrive_info, "Size"))
                log(f"==> code_hashes{br(idx)} == {code_hashes[idx].decode('utf-8')} size={_size} bytes")
                byte_size += _size
                if not is_cached[code_hashes[idx].decode("utf-8")]:
                    size_to_download += _size

        if bool(data_key_dict):
            data_link_file = f"{results_folder_prev}/meta_data_link.json"
            with open(data_link_file, "w") as f:
                json.dump(data_key_dict, f)
        else:
            raise Exception("Something is wrong; data_key_dict is empty")

    output = byte_to_mb(size_to_download)
    log(f"total_size={byte_size} bytes | size to download={size_to_download} bytes => {output} MB", "bold")
    return output, data_key_dict, source_code_key


def _dump_dict_to_file(fn, folder_keys):
    try:
        log("==> meta_data.json file is updated in the parent folder")
        dump_dict_to_file(fn, folder_keys)
    except Exception as e:
        print_tb(e)
        raise e
