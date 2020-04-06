#!/usr/bin/env python3
import os
import subprocess
import time

import git
from config import bp, logging  # noqa: F401
from lib import printc, run_command
from utils import getcwd, getsize, path_leaf

from settings import init_env


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


def is_git_initialized(path, is_in_path=False) -> bool:
    if not is_in_path:
        cwd_temp = getcwd()
        os.chdir(path)
    try:
        repo = git.Repo('.', search_parent_directories=True)
        working_tree_dir = repo.working_tree_dir
    except:
        return False
    finally:
        if not is_in_path:
            os.chdir(cwd_temp)
    return path == working_tree_dir


def git_diff_zip(filename):
    f = open(filename, "w")
    p1 = subprocess.Popen(["git", "diff", "--binary", "HEAD"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["gzip", "-9c"], stdin=p1.stdout, stdout=f)
    p1.stdout.close()
    p2.communicate()
    f.close()


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
        upload everything, changed files!
    """
    success, output = run_command(["git", "config", "core.fileMode", "false"])
    # First ignore deleted files not to be added into git
    success, output = run_command(["bash", f"{env.EBLOCPATH}/bash_scripts/git_ignore_deleted.sh"])
    success, git_head_hash = run_command(["git", "rev-parse", "HEAD"])
    patch_name = f"patch_{git_head_hash}_{source_code_hash}_{index}.diff"

    # File to be uploaded as zip
    patch_file = f"{target_path}/{patch_name}.gz"
    logging.info(f"patch_path={patch_name}.gz")

    repo = git.Repo('.', search_parent_directories=True)
    try:
        repo.git.add(A=True)
        git_diff_zip(patch_file)
    except:
        return False
    finally:
        os.chdir(cwd_temp)

    time.sleep(0.1)
    if not getsize(patch_file):
        logging.info("Created patch file is empty, nothing to upload.")
        is_file_empty = True
        os.remove(patch_file)
    return patch_name, patch_file, is_file_empty


def git_add_all(repo=None):
    if not repo:
        repo = git.Repo('.', search_parent_directories=True)

    # Required for files to be access on the cluster side due to permission issues
    subprocess.run(["chmod", "-R", "775", "."])  # Changes folder's hash
    # subprocess.run(["chmod", "-R", "755", "."])
    # subprocess.run(["chmod", "-R", "775", ".git"])  # https://stackoverflow.com/a/28159309/2402577

    try:
        repo.git.add(A=True)  # git add -A .

        try:
            is_diff = len(repo.index.diff("HEAD"))  # git diff HEAD --name-only | wc -l
            success = True
        except:
            # If it is the first commit HEAD might not exist
            success, is_diff = run_command(["git", "diff", "--cached", "--shortstat"])

        if success and is_diff:
            repo.git.commit('-m', 'update')  # git commit -m update
        return True
    except:
        return False


def git_commit_changes(path) -> bool:
    cwd_temp = getcwd()
    os.chdir(path)
    repo = git.Repo('.', search_parent_directories=True)

    success, output = run_command(["ls", "-l", ".git/refs/heads"])
    if output == "total 0":
        logging.warning("There is no first commit")
    else:
        repo.git.add(A=True)
        if len(repo.index.diff("HEAD")) == 0:
            logging.info(f"{path} is already committed with the given changes.")
            os.chdir(cwd_temp)
            return True
    try:
        git_add_all(repo)
    except Exception as error:
        logging.error(f"E: {error}")
        return False
    finally:
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
