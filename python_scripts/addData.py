import os
import sys

from lib import get_parent_hash, run


def add_to_ipfs(results_folder):
    cmd = ["ipfs", "add", "-r", results_folder]  # uploaded as folder
    try:
        result_ipfs_hash = get_parent_hash(run(cmd))
    except Exception:
        sys.exit()

    if os.path.isdir(results_folder):
        basename = os.path.basename(os.path.normpath(results_folder))
        filepath = os.path.dirname(results_folder)

    print(filepath)
    print(basename)
    # shutil.move(results_folder, filepath + '/' + resultIpfsHash)


results_folder = "/home/netlab/eBlocBroker/DAG"
add_to_ipfs(results_folder)
