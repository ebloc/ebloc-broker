#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Illegal number of parameters. Please add folder path as an argument"
    exit;
fi

if [[ $1 = *".tar.gz" ]]; then
    if [ ! -f $1 ]; then
        echo "File not found! path="$1
        exit
    fi
    md5sum $1 | awk '{print $1}'
    exit
fi

if [[ $1 = *"//"* ]]; then
    echo "E: Please do not use // in your folder path"
    exit 64
fi

target=${1%/}

# Control will enter here if $DIRECTORY doesn't exist.
if [ ! -d "$target" ]; then
    echo 'E: Requested folder does not exit. Please provide complete path, given path='$target
    exit 64
else
    target=$(realpath $target)
fi

machine_os=$(bash $HOME/ebloc-broker/broker/bash_scripts/machine.sh)
if [ "$machine_os" == "Mac" ]; then
    # https://stackoverflow.com/a/4210072/2402577
    #
    # When the -L option is in effect, the -type predicate will always match
    # against the type of the file that a symbolic link points to rather than
    # the link itself
    if  [ "$target" == "." ]; then
        find -L $target \( -name "venv" -o -name "__pycache__" -o -name ".git*" -o -name "node_modules" \) -prune -o -type f \
        -exec md5 -q "$PWD"/{} \; | awk '{print $1}' | sort | md5
    else
        find -L $target \( -name "venv" -o -name "__pycache__" -o -name ".git*" -o -name "node_modules" \) -prune -o -type f \
        -exec md5 -q /{} \; | awk '{print $1}' | sort | md5
    fi
else
    if  [ "$target" == "." ]; then
        find -L $target \( -name "venv" -o -name "__pycache__" -o -name ".git*" -o -name "node_modules" \) -prune -o -type f \
        -exec md5sum "$PWD"/{} \; | awk '{print $1}' | sort | md5sum | awk '{print $1}'
    else
        find -L $target \( -name "venv" -o -name "__pycache__" -o -name ".git*" -o -name "node_modules" \) -prune -o -type f \
        -exec md5sum /{} \; | awk '{print $1}' | sort | md5sum | awk '{print $1}'
    fi
fi
