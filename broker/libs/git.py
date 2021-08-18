#!/usr/bin/env python3

import gzip
import io
import os
import time

import git

from broker.config import env, logging
from broker.libs.ipfs import decrypt_using_gpg
from broker.utils import cd, is_gzip_file_empty, log, path_leaf, run

# from subprocess import CalledProcessError


def initialize_check(path):
    """.git/ folder should exist within the target folder"""
    with cd(path):
        if not is_initialized(path):
            try:
                run(["git", "init", "--initial-branch=master"])
                add_all()
            except Exception as error:
                logging.error(f"E: {error}")
                return False
        return True


def is_initialized(path) -> bool:
    with cd(path):
        try:
            repo = git.Repo(".", search_parent_directories=True)
            working_tree_dir = repo.working_tree_dir
        except:
            return False

        return path == working_tree_dir


def diff_and_gzip(filename):
    repo = git.Repo(".", search_parent_directories=True)
    with gzip.open(filename, "wb") as output:
        # We cannot directly write Python objects like strings!
        # We must first convert them into a bytes format using io.BytesIO() and then write it
        with io.TextIOWrapper(output, encoding="utf-8") as encode:
            encode.write(repo.git.diff("--binary", "HEAD", "--minimal", "--ignore-submodules=dirty"))


def decompress_gzip(filename):
    if not is_gzip_file_empty(filename):
        with gzip.open(filename, "rb") as ip:
            with io.TextIOWrapper(ip, encoding="utf-8") as decoder:
                # Let's read the content using read()
                content = decoder.read()
                print(content)


def diff_patch(path, source_code_hash, index, target_path):
    """
    * "git diff HEAD" for detecting all the changes:
    * Shows all the changes between the working directory and HEAD (which includes changes in the index).
    * This shows all the changes since the last commit, whether or not they have been staged for commit
    * or not.
    """
    sep = "*"  # separator in between the string infos
    is_file_empty = False
    with cd(path):
        log(f"==> Navigate to {path}")
        """TODO
        if not is_initialized(path):
            upload everything, changed files!
        """
        repo = git.Repo(".", search_parent_directories=True)
        try:
            repo.git.config("core.fileMode", "false")  # git config core.fileMode false
            # first ignore deleted files not to be added into git
            run(["bash", f"{env.EBLOCPATH}/broker/bash_scripts/git_ignore_deleted.sh"])
            head_commit_id = repo.rev_parse("HEAD")
            patch_name = f"patch{sep}{head_commit_id}{sep}{source_code_hash}{sep}{index}.diff"
        except:
            return False

        patch_upload_name = f"{patch_name}.gz"  # file to be uploaded as zip
        patch_file = f"{target_path}/{patch_upload_name}"
        logging.info(f"patch_path={patch_upload_name}")

        try:
            repo.git.add(A=True)
            diff_and_gzip(patch_file)
        except:
            return False

    time.sleep(0.25)
    if is_gzip_file_empty(patch_file):
        log("==> Created patch file is empty, nothing to upload")
        os.remove(patch_file)
        is_file_empty = True

    return patch_upload_name, patch_file, is_file_empty


def add_all(repo=None):
    if not repo:
        repo = git.Repo(".", search_parent_directories=True)

    try:
        # subprocess.run(["chmod", "-R", "755", "."])
        # subprocess.run(["chmod", "-R", "775", ".git"])  # https://stackoverflow.com/a/28159309/2402577
        # required for files to be access on the cluster side due to permission issues
        run(["sudo", "chmod", "-R", "775", "."])  # changes folder's hash
    except:
        pass

    try:
        repo.git.add(A=True)  # git add -A .
        try:
            changed_file_len = len(repo.index.diff("HEAD"))  # git diff HEAD --name-only | wc -l
        except:
            # if it is the first commit HEAD might not exist
            changed_file_len = len(repo.git.diff("--cached", "--name-only").split("\n"))

        if changed_file_len > 0:
            repo.git.commit("-m", "update")  # git commit -m update
        return True
    except:
        return False


def commit_changes(path) -> bool:
    with cd(path):
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
                log(f"==> {path} is committed with the given changes using git")
                return True

        try:
            add_all(repo)
        except Exception as e:
            logging.error(f"E: {e}")
            return False
        return True


def apply_patch(git_folder, patch_file, is_gpg=False):
    """Apply git patch.

    https://stackoverflow.com/a/15375869/2402577
    """
    if is_gpg:
        decrypt_using_gpg(patch_file)

    with cd(git_folder):
        base_name = path_leaf(patch_file)
        log(f"==> {base_name}")
        # folder_name = base_name_split[2]
        try:
            # base_name_split = base_name.split("_")
            # git_hash = base_name_split[1]
            # run(["git", "checkout", git_hash])
            # run(["git", "reset", "--hard"])
            # run(["git", "clean", "-f"])

            # echo "\n" >> patch_file.txt seems like fixing it
            with open(patch_file, "a") as myfile:
                myfile.write("\n")

            # output = repo.git.apply("--reject", "--whitespace=fix", patch_file)
            run(["git", "apply", "--reject", "--whitespace=fix", "--verbose", patch_file])
            return True
        except:
            return False


def is_repo(folders):
    for folder in folders:
        with cd(folder):
            if not is_initialized(folder):
                logging.warning(f".git does not exits in {folder}. Applying: `git init`")
                run(["git", "init", "--initial-branch=master"])


def _generate_git_repo(folder):
    log(folder, "green")
    try:
        initialize_check(folder)
        commit_changes(folder)
    except Exception as e:
        raise e


def generate_git_repo(folders):
    """Create git repositories in the given folders if it does not exist."""
    if isinstance(folders, list):
        for folder in folders:
            _generate_git_repo(folder)
    else:  # if string given "/home/user/folder" retreive string instead of "/" with for above
        _generate_git_repo(folders)


# def extract_gzip():
#     pass
