import os
import sys

import libs.ipfs as ipfs


def add_to_ipfs(results_folder):
    try:
        result_ipfs_hash = ipfs.add(results_folder)
        print(result_ipfs_hash)
    except Exception:
        sys.exit()

    if os.path.isdir(results_folder):
        basename = os.path.basename(os.path.normpath(results_folder))
        filepath = os.path.dirname(results_folder)

    print(filepath)
    print(basename)
    # shutil.move(results_folder, filepath + '/' + resultIpfsHash)


results_folder = "/home/alper/DAG"
add_to_ipfs(results_folder)
