#!/usr/bin/env python3

import os
import sys

import libs.git as git

# patch_file = "/home/status -sb201~alper/patch/patch_7bfea156ad612b2a634d0b98e65fe75c815e256d_3cb8e5f14fbd05589469a62017da475d_2.diff"
# git_folder = "/home/alper/base/sourceCode"

patch_file = "/home/alper/_test/source_code/QmTpGQZdJze5grMxRwCotTViahHookwCittmrpMSJ3St2d/patch_f518e8406b65a62c5f92d66de558577b9d3a1d6a_QmR4qfmgQUEQqo8wrPaBVLLB2Z53vTJq9CJmPnu3WwUob6_0.diff.gz.gpg"
git_folder = "/home/alper/_test/source_code"
is_gpg = True

if not os.path.isfile(patch_file):
    print(f"E: {patch_file} file does not exist")
    sys.exit(1)

git.apply_patch(git_folder, patch_file, is_gpg)
