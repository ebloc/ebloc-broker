#!/bin/bash

RED="\033[1;31m"; NC="\033[0m"

if [ "$#" -ne 1 ]; then
    echo -e "${RED}E:${NC} Illegal number of parameters, provide <email>"
    exit 1
fi

keyid=$(gpg --list-secret-keys --keyid-format LONG $1 | sed -n '2p' | tr -d " \t\r")
output=$(gpg --with-colons --fingerprint $keyid | grep fpr | cut -d ':' -f 10 | grep $keyid)
echo $output

# gpg --gen-key
# gpg --list-keys
#
# gpg --list-secret-keys --keyid-format LONG
# ./get_gpg_fingerprint.sh 1D522F92EFA2F330
#
# keyid=$(gpg --list-secret-keys --keyid-format LONG | sed -n '4p' | tr -d " \t\r")
# gpg_fingerprint=$(./get_gpg_fingerprint.sh $keyid)
# echo 0x$gpg_fingerprint

# email=$1
# output=$(gpg --list-secret-keys --keyid-format LONG)
# if [[ "$output" == "" ]]; then
#     echo -e "E: \`gpg --list-secret-keys --keyid-format LONG\` returns empty. Please run: gpg --gen-key"
#     exit 1
# fi

# if [[ $# -ne 1 ]]; then
#     keyid=$(gpg --list-secret-keys --keyid-format LONG | sed -n '4p' | tr -d " \t\r")
#     output=$(gpg --with-colons --fingerprint $keyid | grep fpr | cut -d ':' -f 10 | grep $keyid)
#     echo $output
# else
#     output=$(gpg --with-colons --fingerprint $1 | grep fpr | cut -d ':' -f 10 | grep $1)
#     echo $output
# fi
