#!/usr/bin/env python3

import os
import sys

import libs.git as git
from utils import extract_gzip, log

# patch_file = "/home/status -sb201~alper/patch/patch_7bfea156ad612b2a634d0b98e65fe75c815e256d_3cb8e5f14fbd05589469a62017da475d_2.diff"
# git_folder = "/home/alper/base/source_code"

patch_file = "/home/alper/test_eblocbroker/source_code/patch_da01d178319dfadd0950e205da65bd4fd07e01c8_1-3VQS7OC_Hs3_0TourvSlRa2vkFA3UCc_0.diff.gz"

base_dir = os.path.dirname(patch_file)
base_name = os.path.basename(patch_file).replace(".gz", "")
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
