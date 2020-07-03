#!/usr/bin/env python3
import os
import subprocess
import time

import git

from _tools import bp  # noqa: F401
from config import env, logging
from lib import run, run_command
from utils import getcwd, getsize, path_leaf, printc


def initialize_check(path):
    """.git/ folder should exist within the target folder"""
    cwd_temp = getcwd()
    os.chdir(path)
    if not is_initialized(path, True):
        try:
            run_command(["git", "init"])
            add_all()
        except Exception as error:
            logging.error(f"E: {error}")
            os.chdir(cwd_temp)
            return False
    os.chdir(cwd_temp)
    return True


def is_initialized(path, is_in_path=False) -> bool:
    if not is_in_path:
        cwd_temp = getcwd()
        os.chdir(path)
    try:
        repo = git.Repo(".", search_parent_directories=True)
        working_tree_dir = repo.working_tree_dir
    except:
        return False
    finally:
        if not is_in_path:
            os.chdir(cwd_temp)
    return path == working_tree_dir


def extract_gzip():
    pass


def diff_zip(filename):
    f = open(filename, "w")
    p1 = subprocess.Popen(["git", "diff", "--binary", "HEAD"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["gzip", "-9c"], stdin=p1.stdout, stdout=f)
    p1.stdout.close()
    p2.communicate()
    f.close()


def diff_patch(path, source_code_hash, index, target_path):
    """
    * "git diff HEAD" for detecting all the changes:
    * Shows all the changes between the working directory and HEAD (which includes changes in the index).
    * This shows all the changes since the last commit, whether or not they have been staged for commit or not.
    """
    is_file_empty = False
    printc(path)
    cwd_temp = getcwd()
    os.chdir(path)

    """TODO
    if not is_initialized(path):
        upload everything, changed files!
    """
    try:
        run(["git", "config", "core.fileMode", "false"])
        # first ignore deleted files not to be added into git
        run(["bash", f"{env.EBLOCPATH}/bash_scripts/git_ignore_deleted.sh"])
        git_head_hash = run(["git", "rev-parse", "HEAD"])
        patch_name = f"patch_{git_head_hash}_{source_code_hash}_{index}.diff"
    except:
        return False

    # file to be uploaded as zip
    patch_file = f"{target_path}/{patch_name}.gz"
    logging.info(f"patch_path={patch_name}.gz")

    repo = git.Repo(".", search_parent_directories=True)
    try:
        repo.git.add(A=True)
        diff_zip(patch_file)
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


def add_all(repo=None):
    if not repo:
        repo = git.Repo(".", search_parent_directories=True)

    try:
        # subprocess.run(["chmod", "-R", "755", "."])
        # subprocess.run(["chmod", "-R", "775", ".git"])  # https://stackoverflow.com/a/28159309/2402577
        # required for files to be access on the cluster side due to permission issues
        run(["chmod", "-R", "775", "."])  # changes folder's hash
    except:
        pass

    try:
        repo.git.add(A=True)  # git add -A .
        try:
            is_diff = len(repo.index.diff("HEAD"))  # git diff HEAD --name-only | wc -l
            success = True
        except:
            # if it is the first commit HEAD might not exist
            success, is_diff = run_command(["git", "diff", "--cached", "--shortstat"])

        if success and is_diff:
            repo.git.commit("-m", "update")  # git commit -m update
        return True
    except:
        return False


def commit_changes(path) -> bool:
    cwd_temp = getcwd()
    os.chdir(path)
    repo = git.Repo(".", search_parent_directories=True)

    try:
        output = run(["ls", "-l", ".git/refs/heads"])
    except Exception as e:
        raise Exception("E: Problem on git.commit_changes()") from e

    if output == "total 0":
        logging.warning("There is no first commit")
    else:
        changed_files = [item.a_path for item in repo.index.diff(None)]
        if len(changed_files) > 0:
            logging.info(f"Adding changed files:\{changed_files}")
            repo.git.add(A=True)

        if len(repo.index.diff("HEAD")) == 0:
            logging.info(f"{path} is committed with the given changes")
            os.chdir(cwd_temp)
            return True
    try:
        add_all(repo)
    except Exception as error:
        logging.error(f"E: {error}")
        return False
    finally:
        os.chdir(cwd_temp)

    return True


def apply_patch(git_folder, patch_file):
    cwd_temp = getcwd()
    os.chdir(git_folder)

    base_name = path_leaf(patch_file)
    print(base_name)
    base_name_split = base_name.split("_")
    git_hash = base_name_split[1]
    # folder_name = base_name_split[2]
    try:
        run(["git", "checkout", git_hash])
        run(["git", "reset", "--hard"])
        run(["git", "clean", "-f"])
        logging.info(run(["git", "apply", "--stat", patch_file]))
        logging.info(run(["git", "apply", "--reject", patch_file]))
        return True
    except:
        return False
    finally:
        os.chdir(cwd_temp)


def is_repo(folders) -> bool:
    cwd_temp = getcwd()
    for folder in folders:
        os.chdir(folder)
        if not is_initialized(folder):
            logging.warning(f".git does not exits in {folder}. Applying: `git init`")
            try:
                run(["git", "init"])
            except:
                return False
            finally:
                os.chdir(cwd_temp)

    os.chdir(cwd_temp)
    return True
