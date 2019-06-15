#!/bin/bash 

# Should do sshfs first
# sshfs alper@ebloc.cmpe.boun.edu.tr:/home/alper/eBlocBroker /Users/alper/eB 
 
sourceFolder='/Users/alper/eB'; 
toFolder='/Users/alper/eBlocBroker'; 
 
if [ -z "$(ls -A $sourceFolder)" ]; then 
    echo "Please do: sshfs alper@ebloc.cmpe.boun.edu.tr:/home/alper/eBlocBroker $sourceFolder" 
else 
    rsync -av --progress $sourceFolder/ $toFolder --exclude venv --exclude 'nohup.out' --exclude node_modules --exclude='.git' --exclude /README.md --exclude contract --exclude workflow --exclude webapp --exclude .gitignore --exclude owncloudScripts/oc --exclude rsync.sh --exclude owncloudScripts/password.txt --filter="dir-merge,- .gitignore" --delete 
fi 
