#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Illegal number of parameters. Please add folder path as an argument."
    exit;
fi

if [[ $1 = *".tar.gz" ]]; then
    if [ ! -f $1 ]; then
        echo "File not found! Path="$1
        exit
    fi
    md5sum $1 | awk '{print $1}'
    exit
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

machine_os=$(bash $HOME/eBlocBroker/bash_scripts/machine.sh)
if [ "$machine_os" == "Mac" ]; then
    # doc: https://stackoverflow.com/a/4210072/2402577
    if  [ "$target" == "." ]; then
        find $target \( -name "venv" -o -name "__pycache__" -o -name ".git*" -o -name "node_modules" \) -prune -o -type f \
	-exec md5 -q "$PWD"/{} \; | awk '{print $1}' | sort | md5
    else
        find $target \( -name "venv" -o -name "__pycache__" -o -name ".git*" -o -name "node_modules" \) -prune -o -type f \
	-exec md5 -q /{} \; | awk '{print $1}' | sort | md5
    fi
else
    if  [ "$target" == "." ]; then
        find $target \( -name "venv" -o -name "__pycache__" -o -name ".git*" -o -name "node_modules" \) -prune -o -type f \
	-exec md5sum "$PWD"/{} \; | awk '{print $1}' | sort | md5sum | awk '{print $1}'
    else
        find $target \( -name "venv" -o -name "__pycache__" -o -name ".git*" -o -name "node_modules" \) -prune -o -type f \
	-exec md5sum /{} \; | awk '{print $1}' | sort | md5sum | awk '{print $1}'
    fi
fi
