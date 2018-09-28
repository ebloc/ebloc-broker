#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Illegal number of parameters. Please add folder path as an argument."
    exit;
fi

if [[ $1 = *"//"* ]]; then
    echo "Please do not use // on your folder path."
    exit;
fi

target=${1%/}

# Control will enter here if $DIRECTORY doesn't exist.
if [ ! -d "$target" ]; then
    echo 'Requested folder does not exit. Please provide complete path. Path='$target
    exit
else
    target=$(realpath $target)
fi

machineOS=$(bash $HOME/eBlocBroker/scripts/machine.sh)
if [ "$machineOS" == "Mac" ]; then
    if  [ "$target" == "." ]; then
        find $target -not -path "$target/.git/*" -not -path "$target/.git/hooks/*" -type f \( -exec md5 -q  "$PWD"/{} \; \) | awk '{print $1}' | sort | md5
    else
        find $target -not -path "$target/.git/*" -not -path "$target/.git/hooks/*" -type f \( -exec md5 -q  /{} \; \) | awk '{print $1}' | sort | md5
    fi
else
    if  [ "$target" == "." ]; then
        find $target -not -path "$target/.git/*" -type f \( -exec md5sum "$PWD"/{} \; \) | awk '{print $1}' | sort | md5sum | awk '{print $1}'
    else
        find $target -not -path "$target/.git/*" -type f \( -exec md5sum /{} \; \) | awk '{print $1}' | sort | md5sum | awk '{print $1}'
    fi
fi   


