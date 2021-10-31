#!/usr/bin/env python3

import os
import sys

import broker.libs.git as git
from broker._utils.tools import print_tb
from broker.utils import extract_gzip, log, popen_communicate


def main():
    base_dir = "/home/alper/patch/source_code"
    patch_file_name = (
        "patch*93bbd3a82d2c36b065a67e71b5a6d3edff3eb69d*Qma6SvUzDk6SURtvxrCzNkMbQfNrSyefzNDui3Bozc7JDr*0.diff.gz.gpg"
    )
    patch_file = f"{base_dir}/{patch_file_name}"
    base_name = patch_file_name.replace(".gz", "")
    diff_file_name = f"{base_dir}/{base_name}"
    if not os.path.isfile(diff_file_name):
        breakpoint()  # DEBUG
        if not os.path.isfile(patch_file):
            print(f"E: {patch_file} file does not exist")
            sys.exit(1)
        if patch_file.endswith(".diff.gz"):
            extract_gzip(patch_file)
    else:
        log(f"==> {diff_file_name} exists")

    try:
        git.apply_patch(base_dir, patch_file.replace(".gz", ""), is_gpg=False)
    except Exception as e:
        try:
            # perl -pe 's/\x1b.*?[mGKH]//g' alper.patch > good.patch
            good_patch = f"{base_dir}/good.patch"
            popen_communicate(
                ["perl", "-pe", "s/\x1b.*?[mGKH]//g", "/home/alper/patch/source_code/alper.patch"],
                stdout_file=good_patch,
            )
            git.apply_patch(base_dir, good_patch, is_gpg=False)
        except Exception as e1:
            print_tb(e)
            print_tb(e1)


if __name__ == "__main__":
    main()
