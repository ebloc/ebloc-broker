#!/bin/bash

# gpg --list-secret-keys --keyid-format LONG
# ./get_gpg_fingerprint.sh 1D522F92EFA2F330

output=$(gpg --list-secret-keys --keyid-format LONG)
if [[ "$output" == "" ]]; then
    echo "gpg --list-secret-keys --keyid-format LONG  :returns empty"
    exit 1
fi

if [[ $# -ne 1 ]]; then
    echo "Please provide key_id"
    exit 2
fi

output=$(gpg --with-colons --fingerprint $1 | grep fpr | cut -d ':' -f 10 | grep $1)
echo $output
