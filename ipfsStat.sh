#/!/bin
IPFS_PATH="/home/alper/.ipfs"
export IPFS_PATH
ipfsHash=$1 
timeout 300 ipfs object stat $ipfsHash #wait 5 minutes. TODO: ipfs call should be thread.
