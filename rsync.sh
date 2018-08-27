#!/bin/bash 
 
# sshfs alper@ebloc.cmpe.boun.edu.tr:/home/alper/eBlocBroker /Users/alper/eB 
 
sourceFolder='/Users/alper/eB'; 
toFolder='/Users/alper/eBlocBroker'; 
 
if [ -z "$(ls -A $sourceFolder)" ]; then 
    echo "Please do: sshfs alper@ebloc.cmpe.boun.edu.tr:/home/alper/eBlocBroker $sourceFolder" 
else 
    rsync -av --progress $sourceFolder/ $toFolder --exclude venv --exclude 'nohup.out' --exclude node_modules --exclude='.git' --exclude nodePaths.js --exclude /README.md --exclude contract --exclude .gitignore --filter="dir-merge,- .gitignore" --delete 
fi 
