#!/usr/bin/env python3

import os
import sys

import libs.git as git

# patch_file = "/home/status -sb201~alper/patch/patch_7bfea156ad612b2a634d0b98e65fe75c815e256d_3cb8e5f14fbd05589469a62017da475d_2.diff"
# git_folder = "/home/alper/base/sourceCode"

patch_file = "/home/alper/patch/patch_e8dbd84c366fd438fd3c5786ec3a83892c80865c_a31f01627aad0d8a72c718848169ffbd_2.diff"
git_folder = "/home/alper/base/data/data1"

if not os.path.isfile(patch_file):
    sys.exit(1)

git.apply_patch(git_folder, patch_file)
