import subprocess, shutil, os
from lib import executeShellCommand

def addToIPFS(resultsFolder):
    command = ['ipfs', 'add', '-r', resultsFolder] # Uploaded as folder
    status, resultIpfsHash = executeShellCommand(command, None, True)
    
    p1 = subprocess.Popen(['echo', resultIpfsHash], stdout=subprocess.PIPE)        
    p2 = subprocess.Popen(['tail', '-n1'], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()        
    p3 = subprocess.Popen(['awk', '{print $2}'], stdin=p2.stdout,stdout=subprocess.PIPE)
    p2.stdout.close()        
    resultIpfsHash = p3.communicate()[0].decode('utf-8').strip()
    print("ipfs_hash: " + resultIpfsHash)

    if os.path.isdir(resultsFolder):
        basename=os.path.basename(os.path.normpath(resultsFolder))
        filepath=os.path.dirname(resultsFolder)

    print(filepath)
    print(basename)

    # shutil.move(resultsFolder, filepath + '/' + resultIpfsHash)


resultsFolder="/home/netlab/eBlocBroker/DAG"
addToIPFS(resultsFolder)
