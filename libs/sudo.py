#!/usr/bin/env python3

from subprocess import PIPE, Popen


def _run_as_sudo(sudo_user, cmd_str, shell=False):
    sudo_args = ["sudo", "-u", sudo_user]
    cmd_array = sudo_args + cmd_str.split()
    p, output, error = _popen_communicate(" ".join(cmd_array), shell=shell)

    if p.returncode != 0 or "error" in error:
        raise Exception(error)
    return output


def _popen_communicate(cmd_array, shell=False):
    p = Popen(cmd_array, stdout=PIPE, stderr=PIPE, shell=shell)
    output, error = p.communicate()
    output = output.strip().decode("utf-8")
    error = error.decode("utf-8")
    return p, output, error
