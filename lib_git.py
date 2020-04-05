#!/usr/bin/env python3
import os
import subprocess
import time

from config import bp, logging  # noqa: F401
from lib import printc, run_command, run_command_stdout_to_file
from settings import init_env
from utils import getcwd, getsize, path_leaf


def git_initialize_check(path):
    """ .git/ folder should exist within the target folder"""
    cwd_temp = getcwd()
    os.chdir(path)
    if not is_git_initialized(path, True):
        try:
            run_command(["git", "init"])
            git_add_all()
        except Exception as error:
            logging.error(f"E: {error}")
            os.chdir(cwd_temp)
            return False
    os.chdir(cwd_temp)
    return True


def is_git_initialized(path, is_in_path=False):
    if not is_in_path:
        cwd_temp = getcwd()
        os.chdir(path)
    try:
        output = subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode("utf-8").strip()
    except:
        return False
    finally:
        if not is_in_path:
            os.chdir(cwd_temp)
    return path == output


def git_diff_patch(path, source_code_hash, index, target_path, cloud_storage_id):
    """
    * "git diff HEAD" for detecting all the changes:
    * Shows all the changes between the working directory and HEAD (which includes changes in the index).
    * This shows all the changes since the last commit, whether or not they have been staged for commit or not.
    """
    env = init_env()
    is_file_empty = False
    printc(path)
    cwd_temp = getcwd()
    os.chdir(path)

    """TODO
    if not is_git_initialized(path):
        upload everything
    """
    success, output = run_command(["git", "config", "core.fileMode", "false"])
    # First ignore deleted files not to be added into git
    success, output = run_command(["bash", f"{env.EBLOCPATH}/bash_scripts/git_ignore_deleted.sh"])
    success, git_head_hash = run_command(["git", "rev-parse", "HEAD"])
    patch_name = f"patch_{git_head_hash}_{source_code_hash}_{index}.diff"
    logging.info(f"patch_name={patch_name}")
    patch_file = f"{target_path}/{patch_name}"  # File to be uploaded

    success, output = run_command(["git", "add", "-A", ".", "-v"])
    if not success:
        os.chdir(cwd_temp)
        raise Exception("git could not add files")

    try:
        cmd = ["git", "diff", "--binary", "HEAD"]
        run_command_stdout_to_file(cmd, patch_file)
    except:
        pass

    os.chdir(cwd_temp)
    time.sleep(0.1)
    if not getsize(patch_file):
        logging.info("Created patch file is empty, nothing to upload.")
        is_file_empty = True
        os.remove(patch_file)
    return patch_name, patch_file, is_file_empty


def git_add_all():
    # Required for files to be access on the cluster side due to permission issues
    subprocess.run(["chmod", "-R", "775", "."])  # Changes folder's hash
    # subprocess.run(["chmod", "-R", "755", "."])
    # subprocess.run(["chmod", "-R", "775", ".git"])  # https://stackoverflow.com/a/28159309/2402577
    success, output = run_command(["git", "add", "-A", ".", "-v"])
    success, is_git_cached = run_command(["git", "diff", "--cached", "--name-only"])
    if output or is_git_cached:
        success, output = run_command(["git", "commit", "-m", "update", "-v"])


def git_commit_changes(path) -> bool:
    cwd_temp = getcwd()
    os.chdir(path)

    success, output = run_command(["ls", "-l", ".git/refs/heads"])
    if output == "total 0":
        logging.warning("There is no first commit")
    else:
        # run_command(["git", "config", "core.fileMode", "false"])
        success, output = run_command(["git", "diff", "--binary", "HEAD"])
        if not output:
            logging.info(f"{path} is already committed with the given changes.")
            os.chdir(cwd_temp)
            return True

    try:
        git_add_all()
    except Exception as error:
        logging.error(f"E: {error}")
        return False

    os.chdir(cwd_temp)
    return True


def git_apply_patch(git_folder, patch_file):
    cwd_temp = getcwd()
    os.chdir(git_folder)

    base_name = path_leaf(patch_file)
    print(base_name)
    base_name_split = base_name.split("_")
    git_hash = base_name_split[1]
    # folder_name = base_name_split[2]
    success, output = run_command(["git", "checkout", git_hash])
    run_command(["git", "reset", "--hard"])
    run_command(["git", "clean", "-f"])
    success, output = run_command(["git", "apply", "--stat", patch_file])
    if not success:
        return False

    print(output)
    success, output = run_command(["git", "apply", "--reject", patch_file])
    os.chdir(cwd_temp)


def is_git_repo(folders) -> bool:
    success = True
    cwd_temp = getcwd()
    for idx, folder in enumerate(folders):
        os.chdir(folder)
        if is_git_initialized(folder):
            logging.warning(f".git does not exits in {folder}. Applying: git init")
            success, output = run_command(["git", "init"])
            logging.info(output)
            if not success:
                os.chdir(cwd_temp)
                return False
    os.chdir(cwd_temp)
    return success


def git_pin(ipfs_hash) -> bool:
    cmd = ["ipfs", "pin", "add", ipfs_hash]
    success, output = run_command(cmd, None, True)
    print(output)
    return success
