#!/usr/bin/env python

import git
import gzip
import io
import os
import time
from contextlib import suppress
from git.exc import InvalidGitRepositoryError
from pathlib import Path

from broker import cfg
from broker._utils._log import ok
from broker._utils.tools import remove_ansi_escape_sequence
from broker.utils import cd, is_gzip_file_empty, log, path_leaf, popen_communicate, print_tb, run


def git_init():
    log("Creating an empty Git repository using 'git init'", end="")
    run(["git", "init", "--quiet"])
    run(["git", "reflog", "expire", "--all", "--expire=now"])
    run(["git", "gc", "--prune=now", "--aggressive", "--force"])  # takes few seconds but saves space
    log(ok())


def initialize_check(path):
    """Validate if .git/ folder exist within the target folder."""
    with cd(path):
        if not is_initialized(path):
            try:
                log(f"==> git_repo_dir=\n{path}", is_code=True)
                git_init()
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
            #: checks is the give path top git folder
            *_, output, err = popen_communicate(["git", "rev-parse", "--is-inside-work-tree"])  # noqa
            if output == "true":
                git.Repo(".", search_parent_directories=False)
                return True
        except InvalidGitRepositoryError as e:
            log(f"warning: InvalidGitRepositoryError at path {e}")
            return False
        except Exception as e:
            log(f"warning: {e}")
            return False

        return output == "true"


def diff_and_gzip(fn, home_dir):
    with gzip.open(fn, "wb") as output:
        # We cannot directly write Python objects like strings!
        # We must first convert them into a bytes format using io.BytesIO() and then write it
        with io.TextIOWrapper(output, encoding="utf-8") as encode:
            cmd = [
                "env",
                f"HOME={home_dir}",
                "git",
                "diff",
                "--binary",
                "HEAD",
                "--minimal",
                "--ignore-submodules=dirty",
                "--color=never",
            ]
            encode.write(run(cmd))


# def diff_and_gzip_repo(fn):
#     repo = git.Repo(".", search_parent_directories=True)
#     with gzip.open(fn, "wb") as output:
#         with io.TextIOWrapper(output, encoding="utf-8") as encode:
#             encode.write(repo.git.diff("--binary", "HEAD", "--minimal", "--ignore-submodules=dirty", "--color=never"))


def decompress_gzip(fn):
    if not is_gzip_file_empty(fn):
        with gzip.open(fn, "rb") as ip:
            with io.TextIOWrapper(ip, encoding="utf-8") as decoder:
                content = decoder.read()
                log(content)


def diff_patch(path: Path, source_code_hash, index, target_path, home_dir):
    """Apply diff patch.

    "git diff HEAD" for detecting all the changes:
    Shows all the changes between the working directory and HEAD (which includes changes in the index).
    This shows all the changes since the last commit, whether or not they have been staged for commit
    or not.
    """
    is_file_empty = False
    with cd(path):
        log(f"==> Navigated into {path}")
        """TODO
        if not is_initialized(path):
            upload everything, changed files!
        """
        try:
            # os.environ["HOME"] = str(home_dir)  # needed if repo is used
            #: https://stackoverflow.com/a/52227100/2402577
            run(["env", f"HOME={home_dir}", "git", "config", "--global", "--add", "safe.directory", path])
            run(["env", f"HOME={home_dir}", "git", "config", "core.fileMode", "false"])
            # first ignore deleted files not to be added into git ignore deleted
            # files to prevent them to added into git commit which will increase the file size
            output = run(["env", f"HOME={home_dir}", "git", "status"])
            for line in output.split("\n"):
                if "deleted:" in line:
                    fn = line.replace("deleted:", "").strip().replace(" ", "")
                    fn = remove_ansi_escape_sequence(fn)
                    with suppress(Exception):
                        run(["env", f"HOME={home_dir}", "git", "update-index", "--assume-unchanged", fn])

            # head_commit_id = repo.rev_parse("HEAD")
            head_commit_id = run(["env", f"HOME={home_dir}", "git", "rev-parse", "HEAD"])
            sep = "~"  # separator in between the string infos
            patch_name = f"patch{sep}{head_commit_id}{sep}{source_code_hash}{sep}{index}.diff"
        except Exception as e:
            print_tb(e)
            return False

        patch_upload_fn = f"{patch_name}.gz"  # file to be uploaded as zip
        patch_file = f"{target_path}/{patch_upload_fn}"
        log(f"patch_path=[m]{patch_upload_fn}", h=False)
        try:
            run(["env", f"HOME={home_dir}", "git", "add", "-A"])
            diff_and_gzip(patch_file, home_dir)
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


def add_all_(_env):
    """Add all into git using bare git."""
    try:
        log(
            "all files in the entire working tree are updated in the Git repository",
            end="",
        )
        run(["git", "add", "-A"], env=_env)
        log(ok())
        try:
            cmd = ["git", "diff-index", "HEAD", "--ignore-blank-lines", "--ignore-space-at-eol", "--shortstat"]
            output = run(cmd, env=_env)
            changed_file_count = int(output.split("files changed", 1)[0])
        except:
            cmd = ["git", "diff", "--cached", "--ignore-blank-lines", "--ignore-space-at-eol", "--shortstat"]
            output = run(cmd, env=_env)
            changed_file_count = int(output.split("files changed", 1)[0])

        if changed_file_count > 0:
            log("Record changes to the repository", end="")
            run(["git", "commit", "-m", "update"], env=_env)
            log(ok())
    except Exception as e:
        print_tb(e)
        raise e


def commit_m_update(repo):
    log("Running: 'git commit -m update' ", end="")
    for attempt in range(10):
        try:
            repo.git.commit("-m", "update")  # here
            log(ok())
        except Exception as e:
            if "nothing to commit" in str(e):
                return

            log(f"E: {e} | attempt={attempt}")
            if attempt == 9:
                print_tb(e)
            else:
                time.sleep(5)

    # to continue test do not raise Exception
    # raise Exception("Exception for: 'git commit -m update'")


def add_all(repo=None):
    """Add all into git."""
    try:
        if not repo:
            repo = git.Repo(".", search_parent_directories=True)

        log("all files in the entire working tree are updated in the Git repository", end="")
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
            log("Record changes to the repository...")
            commit_m_update(repo)
    except Exception as e:
        print_tb(e)
        raise e


def commit_changes(path):
    with cd(path):
        repo = git.Repo(".", search_parent_directories=True)
        try:
            output = run(["ls", "-l", ".git/refs/heads"])
        except Exception as e:
            raise Exception("Problem on git.commit_changes()") from e

        if output == "total 0":
            log("warning: there is no first commit")
        else:
            changed_files = [item.a_path for item in repo.index.diff(None)]
            if len(changed_files) > 0:
                log("==> adding changed files:")
                for _file in changed_files:
                    log(_file, "blue")

                repo.git.add(A=True)

            if len(repo.index.diff("HEAD")) == 0:
                log(f"==> {path} is\n    committed with the given changes using git")

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
    if os.stat(patch_file).st_size == 0:
        log(f"warning: patch_file={patch_file} is empty")
        return

    if is_gpg:
        cfg.ipfs.decrypt_using_gpg(patch_file)

    with cd(git_folder):
        base_name = path_leaf(patch_file)
        log(f"==> [m]{base_name}")
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
            # "--allow-empty",
            "--verbose",
            patch_file,
        ]
        cmd_summary = cmd.copy()
        cmd_summary.insert(3, "--summary")
        output = run(cmd_summary)
        log(output)
        output = run(cmd)
        log(output)


def is_repo(folders) -> None:
    for folder in folders:
        if not isinstance(folder, bytes):
            with cd(folder):
                if not is_initialized(folder):
                    log(f"warning: {folder} doesn't have a git repository. ", end="")
                    git_init()


def _generate_git_repo(folder):
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
