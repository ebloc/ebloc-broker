#!/bin/bash

# gpg --list-secret-keys --keyid-format LONG
# ./get_gpg_fingerprint.sh 1D522F92EFA2F330

output=$(gpg --with-colons --fingerprint $1 | grep fpr | cut -d ':' -f 10 | grep $1)
echo $output
