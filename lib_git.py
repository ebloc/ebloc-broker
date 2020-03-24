#!/usr/bin/env python3
import os
import subprocess
import sys
import time

from config import bp, logging  # noqa: F401
from lib import printc, run_command, run_command_stdout_to_file
from utils import getcwd, path_leaf


def git_diff_patch(path, source_code_hash, index, results_folder_prev) -> bool:
    """
    * "git diff HEAD" for detecting all the changes:
    * Shows all the changes between the working directory and HEAD (which includes changes in the index).
    * This shows all the changes since the last commit, whether or not they have been staged for commit or not.
    """
    printc(path)
    cwd_temp = getcwd()
    os.chdir(path)
    success, git_head_hash = run_command(["git", "rev-parse", "HEAD"])
    patch_name = f"patch_{git_head_hash}_{source_code_hash}_{index}.diff"
    logging.info(f"patch_name={patch_name}")
    # File to be uploaded
    patch_file = f"{results_folder_prev}/{patch_name}"

    success, output = run_command(["git", "add", "-A", ".", "-v"])
    if not success:
        sys.exit(1)

    cmd = ["git", "diff", "--binary", "HEAD"]
    success = run_command_stdout_to_file(cmd, patch_file)
    os.chdir(cwd_temp)
    time.sleep(0.1)
    return success, patch_name, patch_file


def git_commit_changes(path) -> bool:
    cwd_temp = getcwd()
    os.chdir(path)
    # run_command(["git", "config", "core.fileMode", "false"])
    success, output = run_command(["git", "diff", "--binary", "HEAD"])
    if not output:
        logging.info(f"{path} is already committed with the given changes.")
        os.chdir(cwd_temp)
        return True
    try:
        # Required for files to be access on the cluster side due to permission issues
        subprocess.run(["chmod", "-R", "775", "."])  # Changes folder's hash
        # subprocess.run(["chmod", "-R", "755", "."])
        # subprocess.run(["chmod", "-R", "775", ".git"])  # https://stackoverflow.com/a/28159309/2402577
        success, output = run_command(["git", "add", "-A", ".", "-v"])
        success, is_git_cached = run_command(["git", "diff", "--cached", "--name-only",])
        if output or is_git_cached:
            success, output = run_command(["git", "commit", "-m", "update", "-v"])

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
        _path = getcwd()
        succuss, output = run_command(["git", "rev-parse", "--show-toplevel"])
        if _path != output:
            logging.warning(f".git does not exits in {folder}. Applying: git init")
            success, output = run_command(["git", "init"])
            logging.info(output)
            if not success:
                os.chdir(cwd_temp)
                return False
    os.chdir(cwd_temp)
    return success
