#!/bin/bash

# Should do sshfs first
# sshfs alper@ebloc.cmpe.boun.edu.tr:/home/alper/eBlocBroker /Users/alper/eB

sourceFolder='/Users/alper/eB';
toFolder='/Users/alper/eBlocBroker';

while true; do
    read -p "> Do you wish to rsync from TETAM server? (y/n) " yn
    case $yn in
        [Yy]* ) break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

if [ -z "$(ls -A $sourceFolder)" ]; then
    echo "Please do: sshfs alper@ebloc.cmpe.boun.edu.tr:/home/alper/eBlocBroker $sourceFolder"
else
    rsync -av --progress $sourceFolder/ $toFolder --exclude venv --exclude 'nohup.out' --exclude node_modules --exclude='.git' --exclude /README.md --exclude contract --exclude workflow --exclude webapp --exclude .gitignore --exclude owncloudScripts/oc --exclude rsync.sh --exclude owncloudScripts/password.txt --exclude contractCalls/contract.json --exclude contractCalls/abi.json --filter="dir-merge,- .gitignore" --delete
fi
