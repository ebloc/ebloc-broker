#!/bin/bash

# Should do sshfs first
# sshfs alper@ebloc.cmpe.boun.edu.tr:/home/alper/ebloc-broker /Users/alper/eB

source_folder='$HOME/eB';
to_folder='$HOME/ebloc-broker';

while true; do
    read -p "[ebloc-broker] Would you like to rsync from TETAM server? [Y/n]:" yn
    case $yn in
        [Yy]* ) break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no";;
    esac
done

if [ -z "$(ls -A $source_folder)" ]; then
    echo "Please do: sshfs alper@ebloc.cmpe.boun.edu.tr:/home/alper/ebloc-broker $source_folder"
    echo "Please do: sshfs netlab@193.140.196.159:/home/netlab/ebloc-broker $source_folder"
else
    rsync -av --progress $source_folder/ $to_folder --exclude .mypy_cache --exclude venv --exclude \
          'nohup.out' --exclude node_modules --exclude='.git' --exclude /README.md --exclude contract \
          --exclude workflow --exclude webapp --exclude .gitignore --exclude owncloudScripts/oc \
          --exclude bash_scripts/rsync.sh --exclude owncloudScripts/password.txt \
          --exclude eblocbroker/contract.json --exclude eblocbroker/abi.json \
          --filter="dir-merge,- .gitignore" --delete
fi
