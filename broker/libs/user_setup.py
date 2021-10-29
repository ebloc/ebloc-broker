#!/usr/bin/env python3

import hashlib
import os
import pwd

from broker._utils.tools import mkdir
from broker.config import logging
from broker.lib import run
from broker.libs.slurm import add_user_to_slurm
from broker.utils import _remove, log, popen_communicate  # noqa: F401


def remove_user(user_name, user_dir):
    """
    # for test purposes
    sudo userdel $USERNAME
    sudo rm -rf $BASEDIR/$USERNAME
    sacctmgr remove user where user=$USERNAME --immediate
    """
    run(["sudo", "userdel", "--force", user_name])
    cmd = ["sacctmgr", "remove", "user", "where", f"user={user_name}", "--immediate"]
    p, output, *_ = popen_communicate(cmd)
    if p.returncode != 0 and "Nothing deleted" not in output:
        logging.error(f"E: sacctmgr remove error: {output}")
        raise
    # _remove(user_dir)
    # remove_user(user)


def username_check(check):
    """Check if username exists."""
    try:
        pwd.getpwnam(check)
        log("user %s exists" % (check))
        return False
    except KeyError:
        log("user %s does not exist. Continuing... %s" % (check, check))
        return True


def give_rwe_access(user, path):
    """Give Read/Write/Execute access to the given user on the give folder."""
    run(["sudo", "setfacl", "-R", "-m", f"user:{user}:rwx", path])


def set_folder_permission(path, user_name, slurm_user):
    # block others and people in the same group to do read/write/execute
    run(["sudo", "chmod", "700", path])

    # give Read/Write/Execute access to USER on the give folder
    give_rwe_access(user_name, path)

    # give Read/Write/Execute access to root user on the give folder
    give_rwe_access(slurm_user, path)

    # Inserting user into the eblocbroker group
    # cmd: sudo usermod -a -G eblocbroker ebdf86b0ad4765fda68158489cec9908
    run(["sudo", "usermod", "-L", "-a", "-G", "eblocbroker", user_name])


def user_add(user_address, basedir, slurm_user):
    logging.info("adding user")
    # convert ethereum user address into 32-bits
    user_name = hashlib.md5(user_address.encode("utf-8")).hexdigest()
    user_dir = f"{basedir}/{user_name}"
    add_user_to_slurm(user_name)

    if username_check(user_name):
        run(["sudo", "useradd", "-d", user_dir, "-m", user_name, "--shell", "/bin/bash"])
        log(f"{user_address} => {user_name}) is added as user", "yellow")
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
            # force to add user to slurm
            add_user_to_slurm(user_name)
            mkdir(f"{user_dir}/cache")
        else:
            log(f"{user_address} => {user_name} has already been created", "bold yellow")


if __name__ == "__main__":
    # 0xabd4f78b6a005bdf7543bc2d39edf07b53c926f4
    user_add("0xabd4fs8b6a005bdf7543bc2d39eds08b53c926q0", "/var/eBlocBroker", "netlab")
    print("done")
