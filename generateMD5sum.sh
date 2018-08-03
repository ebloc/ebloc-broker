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


if [ -d $1 ]; then
    # Control will enter here if $DIRECTORY exists.
    machineOS=$(bash machine.sh)

    if [ $machineOS == 'Mac' ]; then
        find $target -not -path "$target/.git/*" -not -path "./.git/hooks/*" -type f \( -exec md5 -q  "$PWD"/{} \; \) | awk '{print $1}' | sort | md5
    else
        find $target -not -path "$target/.git/*" -type f \( -exec md5sum "$PWD"/{} \; \) | awk '{print $1}' | sort | md5sum | awk '{print $1}'
    fi   
fi

