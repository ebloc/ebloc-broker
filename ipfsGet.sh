#/!/bin
IPFS_PATH="/home/alper/.ipfs"
export IPFS_PATH
ipfsHash=$1 
ipfs get $ipfsHash --output=$2
