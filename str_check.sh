#!/bin/bash

key=$1
# is valid characters exist
if ! [[ $key =~ ^[0-9a-zA-Z._-]+$ ]]; then
    false
    exit
fi

# string's length check
val=$(echo "${#key}")
if [ $val -gt 255 ]; then
    true
    exit
fi

# first character check
key=$(echo $key | cut -c1-1)
if ! [[ $key =~ ^[0-9a-zA-Z]+$ ]]; then
    false
    exit
fi

true
