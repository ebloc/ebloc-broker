#!/usr/bin/env python3

import os
import sys

import broker.libs.git as git
from broker.utils import extract_gzip, log


def main():
    base_dir = "/home/alper/test_eblocbroker/source_code"
    patch_file_name = (
        "patch*3eaec34e259de7b3214b01ee691fda2dde0cb178*QmRD841sowPfgz8u2bMBGA5bYAAMPXxUb4J95H7YjngU4K*9.diff.gz"
    )
    patch_file = f"{base_dir}/{patch_file_name}"

    base_name = patch_file_name.replace(".gz", "")
    diff_file_name = f"{base_dir}/{base_name}"

    if not os.path.isfile(diff_file_name):
        if not os.path.isfile(patch_file):
            print(f"E: {patch_file} file does not exist")
            sys.exit(1)
        if patch_file.endswith(".diff.gz"):
            extract_gzip(patch_file)
    else:
        log(f"==> {diff_file_name} exists")

    git.apply_patch(base_dir, patch_file.replace(".gz", ""), is_gpg=False)


if __name__ == "__main__":
    main()
