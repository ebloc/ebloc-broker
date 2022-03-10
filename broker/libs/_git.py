#!/usr/bin/env python3

import gzip
import io
import os
import time
from contextlib import suppress
from pathlib import Path

import git
from git.exc import InvalidGitRepositoryError

from broker import cfg
from broker._utils._log import ok
from broker.config import env, logging
from broker.utils import cd, is_gzip_file_empty, log, path_leaf, popen_communicate, print_tb, run


def initialize_check(path):
    """Validate if .git/ folder exist within the target folder."""
    with cd(path):
        if not is_initialized(path):
            try:
                log(f"## git_repo={path}")
                log("Creating an empty Git repository ", end="")
                run(["git", "init", "--initial-branch=master"])
                log(ok())
                add_all()
            except Exception as e:
                log(f"E: {e}")
                raise e


def is_initialized(path) -> bool:
    """Check whether given the path is initialized with git.

    __ https://stackoverflow.com/a/16925062/2402577
    """
    with cd(path):
        try:
            *_, output, err = popen_communicate(["git", "rev-parse", "--is-inside-work-tree"])  # noqa
            if output == "true":
                #: checks is the give path top git folder
                git.Repo(".", search_parent_directories=False)
                return True
        except InvalidGitRepositoryError as e:
            log(f"warning: InvalidGitRepositoryError at path {e}")
            return False
        except Exception as e:
            log(f"warning: {e}")
            return False

        return output == "true"


def diff_and_gzip(filename):
    repo = git.Repo(".", search_parent_directories=True)
    with gzip.open(filename, "wb") as output:
        # We cannot directly write Python objects like strings!
        # We must first convert them into a bytes format using io.BytesIO() and then write it
        with io.TextIOWrapper(output, encoding="utf-8") as encode:
            encode.write(repo.git.diff("--binary", "HEAD", "--minimal", "--ignore-submodules=dirty", "--color=never"))


def decompress_gzip(filename):
    if not is_gzip_file_empty(filename):
        with gzip.open(filename, "rb") as ip:
            with io.TextIOWrapper(ip, encoding="utf-8") as decoder:
                content = decoder.read()
                log(content)


def diff_patch(path: Path, source_code_hash, index, target_path):
    """Apply diff patch.

    "git diff HEAD" for detecting all the changes:
    Shows all the changes between the working directory and HEAD (which includes changes in the index).
    This shows all the changes since the last commit, whether or not they have been staged for commit
    or not.
    """
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
            run([env.BASH_SCRIPTS_PATH / "git_ignore_deleted.sh"])
            head_commit_id = repo.rev_parse("HEAD")
            sep = "~"  # separator in between the string infos
            patch_name = f"patch{sep}{head_commit_id}{sep}{source_code_hash}{sep}{index}.diff"
        except:
            return False

        patch_upload_fn = f"{patch_name}.gz"  # file to be uploaded as zip
        patch_file = f"{target_path}/{patch_upload_fn}"
        logging.info(f"patch_path={patch_upload_fn}")
        try:
            repo.git.add(A=True)
            diff_and_gzip(patch_file)
        except:
            return False

    time.sleep(0.25)
    if is_gzip_file_empty(patch_file):
        log("==> created patch file is empty, nothing to upload")
        with suppress(Exception):
            os.remove(patch_upload_fn)
            os.remove(patch_file)

        is_file_empty = True

    return patch_upload_fn, patch_file, is_file_empty


def add_all(repo=None):
    """Add all into git."""
    try:
        if not repo:
            repo = git.Repo(".", search_parent_directories=True)

        log("all files in the entire working tree are updated in the Git repository ", end="")
        repo.git.add(A=True)
        log(ok())
        try:
            #: git diff HEAD --name-only | wc -l
            changed_file_len = len(repo.index.diff("HEAD", ignore_blank_lines=True, ignore_space_at_eol=True))
        except:
            # if it is the first commit HEAD might not exist
            changed_file_len = len(
                repo.git.diff("--cached", "--ignore-blank-lines", "--ignore-space-at-eol", "--name-only").split("\n")
            )

        if changed_file_len > 0:
            log("Record changes to the repository ", end="")
            repo.git.commit("-m", "update")
            log(ok())
    except Exception as e:
        print_tb(e)
        raise e


def commit_changes(path):
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
                log("==> adding changed files:")
                for _file in changed_files:
                    log(_file, "bold")

                repo.git.add(A=True)

            if len(repo.index.diff("HEAD")) == 0:
                log(f"==> {path}\n    is committed with the given changes using git")

        try:
            add_all(repo)
        except Exception as e:
            log(f"E: {e}")
            raise e


def apply_patch(git_folder, patch_file, is_gpg=False):
    """Apply git patch.

    output = repo.git.apply("--reject", "--whitespace=fix",
               "--ignore-space-change", "--ignore-whitespace", "--verbose", patch_file)

    __ https://stackoverflow.com/a/15375869/2402577
    """
    if is_gpg:
        cfg.ipfs.decrypt_using_gpg(patch_file)

    with cd(git_folder):
        base_name = path_leaf(patch_file)
        log(f"==> [magenta]{base_name}")
        # folder_name = base_name_split[2]
        #
        # base_name_split = base_name.split("_")
        # git_hash = base_name_split[1]
        # run(["git", "checkout", git_hash])
        # run(["git", "reset", "--hard"])
        # run(["git", "clean", "-f"])
        # echo "\n" >> patch_file.txt seems like fixing it
        #
        # with open(patch_file, "a") as myfile:
        #     myfile.write("\n")
        cmd = [
            "git",
            "apply",
            "--reject",
            "--whitespace=fix",
            "--ignore-space-change",
            "--ignore-whitespace",
            "--verbose",
            patch_file,
        ]  # ,is_quiet=True,
        cmd_summary = cmd.copy()
        cmd_summary.insert(3, "--summary")
        output = run(cmd_summary)
        log(output)
        output = run(cmd)
        log(output)


def is_repo(folders):
    for folder in folders:
        if not isinstance(folder, bytes):
            with cd(folder):
                if not is_initialized(folder):
                    log(f"warning: .git does not exits in {folder}. Applying: git init ", end="")
                    run(["git", "init", "--initial-branch=master"])
                    log(ok())


def _generate_git_repo(folder):
    log(folder, "green")
    try:
        initialize_check(folder)
        commit_changes(folder)
    except Exception as e:
        raise e


def generate_git_repo(folders):
    """Create git repositories in the given folders if it does not exist.

    IMPORTANT NOTE: consider ignoring to push .git into the submitted folder
    """
    if isinstance(folders, list):
        for folder in folders:
            if not isinstance(folder, bytes):
                _generate_git_repo(folder)
    else:
        if not isinstance(folders, bytes):
            _generate_git_repo(folders)


# def extract_gzip():
#     pass
