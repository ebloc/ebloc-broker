import subprocess, shutil, os
from lib import executeShellCommand, getIpfsParentHash

def addToIPFS(resultsFolder):
    command = ['ipfs', 'add', '-r', resultsFolder] # Uploaded as folder
    status, result = executeShellCommand(command, None, True)
    resultIpfsHash = lib.getIpfsParentHash(result)
    
    if os.path.isdir(resultsFolder):
        basename=os.path.basename(os.path.normpath(resultsFolder))
        filepath=os.path.dirname(resultsFolder)

    print(filepath)
    print(basename)
    # shutil.move(resultsFolder, filepath + '/' + resultIpfsHash)


resultsFolder="/home/netlab/eBlocBroker/DAG"
addToIPFS(resultsFolder)
