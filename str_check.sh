#!/bin/bash

key=$1
# Is valid characters exist
if ! [[ $key =~ ^[0-9a-zA-Z._-]+$ ]]; then
    echo 'False'; exit
fi

# String's length check
val=$(echo "${#key}")
if [ $val -gt 255 ];
   then echo "False"; exit
fi

# First character check
key=$(echo $key | cut -c1-1)
if ! [[ $key =~ ^[0-9a-zA-Z]+$ ]]; then
    echo 'False'; exit
fi

echo 'True';
