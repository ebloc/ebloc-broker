#!/usr/bin/env python3

import os
import sys
from os.path import expanduser
from pathlib import Path

import broker.libs._git as git
from broker._utils.tools import print_tb
from broker.utils import extract_gzip, log, popen_communicate


def appy_patch(base_dir, patch_fn):
    r"""Apply path file.

    cmd: perl -pe 's/\x1b.*?[mGKH]//g' alper.patch > good.patch
    """
    patch_file = f"{base_dir}/{patch_fn}"
    base_name = patch_fn.replace(".gz", "")
    diff_file_name = f"{base_dir}/{base_name}"
    if not os.path.isfile(diff_file_name):
        if not os.path.isfile(patch_file):
            print(f"E: {patch_file} file does not exist")
            sys.exit(1)

        if patch_file.endswith(".diff.gz"):
            extract_gzip(patch_file)
    else:
        log(f"==> [magenta]{diff_file_name}[/magenta] exists")

    try:
        git.apply_patch(base_dir, patch_file.replace(".gz", ""), is_gpg=False)
    except Exception as e:
        print_tb(e)
        try:
            good_patch = f"{base_dir}/good.patch"
            sep = "~"
            popen_communicate(
                ["perl", "-pe", "s/\x1b.*?[mGKH]//g", str(Path(patch_file)).replace(f"{sep}", f"\{sep}")],
                stdout_fn=good_patch,
            )
            git.apply_patch(base_dir, good_patch, is_gpg=False)
        except Exception as e1:
            print_tb(e1)


def main(base_dir, patch_fn):
    appy_patch(base_dir, patch_fn)


if __name__ == "__main__":
    base_dir = expanduser("~/test_eblocbroker/test_data/base/source_code")
    patch_fn = "patch~f5fae5edf523c00f3f033af668f78663bf331091~QmYhNZrnG9Tj2ay5HbRWxp4Lr8i4pbiDV3ddWz32u4Cvzb~0.diff.gz"
    main(base_dir, patch_fn)
