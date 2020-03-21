#!/usr/bin/env python3
import os
import subprocess
import sys
import time

from config import bp, logging  # noqa: F401
from lib import run_command, run_command_stdout_to_file
from utils import getcwd


def git_diff_patch(path, target_file) -> bool:
    """
    * "git diff HEAD" for detecting all the changes:
    * Shows all the changes between the working directory and HEAD (which includes changes in the index).
    * This shows all the changes since the last commit, whether or not they have been staged for commit or not.
    """
    cwd_temp = getcwd()
    os.chdir(path)
    success, output = run_command(["git", "add", "-A", ".", "-v"])
    if not success:
        sys.exit(1)

    cmd = ["git", "diff", "HEAD"]
    success = run_command_stdout_to_file(cmd, target_file)
    os.chdir(cwd_temp)
    time.sleep(0.1)
    return success


def git_commit_changes(path) -> bool:
    cwd_temp = getcwd()
    os.chdir(path)
    # run_command(["git", "config", "core.fileMode", "false"])
    try:
        # Required for files to be access on the cluster side due to permission issues
        subprocess.run(["chmod", "-R", "775", "."])
        # subprocess.run(["chmod", "-R", "755", "."])
        # subprocess.run(["chmod", "-R", "775", ".git"])  # https://stackoverflow.com/a/28159309/2402577
        success, output = run_command(["git", "add", "-A", ".", "-v"])
        success, is_git_cached = run_command(["git", "diff", "--cached", "--name-only"])
        if output or is_git_cached:
            success, output = run_command(["git", "commit", "-m", "update", "-v"])

    except Exception as error:
        logging.error(f"E: {error}")
        return False

    os.chdir(cwd_temp)
    return True


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
