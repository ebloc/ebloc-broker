#!/usr/bin/env python3

import hashlib
import os
import pwd

from broker._utils._log import log, ok
from broker._utils.tools import _remove, mkdir
from broker.config import env
from broker.lib import run
from broker.libs.slurm import add_user_to_slurm
from broker.utils import popen_communicate  # noqa: F401


def remove_user(user_name, user_dir=None):
    """Remove user from Slurm.

    # for test purposes
    sudo userdel $USERNAME
    sudo rm -rf $BASEDIR/$USERNAME
    sacctmgr remove user where user=$USERNAME --immediate
    """
    run(["sudo", "userdel", "--force", user_name])
    cmd = ["sacctmgr", "remove", "user", "where", f"user={user_name}", "--immediate"]
    p, output, *_ = popen_communicate(cmd)
    if p.returncode != 0 and "Nothing deleted" not in output:
        raise Exception(f"sacctmgr remove error: {output}")

    # remove_user(user)
    if user_dir:
        _remove(user_dir)


def username_check(username):
    """Check whether username exists."""
    try:
        pwd.getpwnam(username)
        log(f"## user=[blue]{username}[/blue] exists")
        return False
    except KeyError:
        log(f"user {username} does not exist. Continuing...")
        return True


def give_rwe_access(user, path):
    """Give read/write/execute access to the given user on the given folder."""
    run(["sudo", "setfacl", "-R", "-m", f"user:{user}:rwx", path])


def set_folder_permission(path, user_name, slurm_user):
    # block others and people in the same group to do read/write/execute
    run(["sudo", "chmod", "700", path])

    #: give read/write/execute access to USER on the given folder
    give_rwe_access(user_name, path)

    #: give read/write/execute access to root user on the given folder
    give_rwe_access(slurm_user, path)

    # insert user into the eblocbroker group
    # __ cmd: sudo usermod -a -G eblocbroker ebdf86b0ad4765fda68158489cec9908
    run(["sudo", "usermod", "-L", "-a", "-G", "eblocbroker", user_name])


def user_add(user_address, basedir, slurm_user):
    user_address = user_address.lower()
    log(f"## adding user=[m]{user_address}[/m]", end="")
    try:  # convert ethereum user address into 32-bits
        user_name = hashlib.md5(user_address.encode("utf-8")).hexdigest()
        log(f" | user_name={user_name}")
    except Exception as e:
        log()
        log(f"warning: user_address={user_address}")
        raise e

    user_dir = f"{basedir}/{user_name}"
    add_user_to_slurm(user_name)
    if username_check(user_name):
        run(["sudo", "useradd", "-d", user_dir, "-m", user_name, "--shell", "/bin/bash"])
        log(f"[pink]{user_address}[/pink] => [yellow]{user_name}[/yellow]) added as user", h=False)
        try:
            set_folder_permission(user_dir, user_name, slurm_user)
            add_user_to_slurm(user_name)
            mkdir(f"{user_dir}/cache")
        except:
            run(["sudo", "userdel", "--force", user_name])
    else:
        if not os.path.isdir(user_dir):
            log(f"{user_address} => {user_name} does not exist. Attempting to read the user", "yellow")
            run(["sudo", "userdel", "--force", user_name])
            run(["sudo", "useradd", "-d", user_dir, "-m", user_name])
            set_folder_permission(user_dir, user_name, slurm_user)
            log(f"{user_address} => {user_name} is created", "yellow")
            add_user_to_slurm(user_name)  # force to add user to slurm
            try:
                mkdir(f"{user_dir}/cache")
            except:
                give_rwe_access(env.SLURMUSER, user_dir)
                mkdir(f"{user_dir}/cache")

        else:
            log(f"## [m]{user_address}[/m] => [blue]{user_name}[/blue] has already been created")


def main():
    # 0xabd4f78b6a005bdf7543bc2d39edf07b53c926f4
    user_add("0xabd4fs8b6a005bdf7543bc2d39eds08b53c926q0", "/var/ebloc-broker", "netlab")
    log(ok())


if __name__ == "__main__":
    main()
