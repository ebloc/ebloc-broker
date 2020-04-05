import os

from lib import execute_shell_cmd, get_ipfs_parent_hash


def addToIPFS(results_folder):
    cmd = ["ipfs", "add", "-r", results_folder]  # Uploaded as folder
    success, output = execute_shell_cmd(cmd, None, True)
    success, result_ipfs_hash = get_ipfs_parent_hash(output)

    if os.path.isdir(results_folder):
        basename = os.path.basename(os.path.normpath(results_folder))
        filepath = os.path.dirname(results_folder)

    print(filepath)
    print(basename)
    # shutil.move(results_folder, filepath + '/' + resultIpfsHash)


results_folder = "/home/netlab/eBlocBroker/DAG"
addToIPFS(results_folder)
