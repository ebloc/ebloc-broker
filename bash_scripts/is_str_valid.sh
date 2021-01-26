#!/bin/bash

string=$1
key_first_char=$(echo $string | cut -c1-1)
if [[ $string == "" ]]; then
    echo "E: provided string is empty"
    false
   exit
fi

if [[ $string == "." ]] || [[ $string == ".." ]]; then
    # "." and ".." are added automatically and always exist, so you can't have a
    # file named . or .. // https://askubuntu.com/a/416508/660555
    echo "E: filename cannot be '.' or '..'"
    false
    exit
fi

key_len=$(echo "${#string}")
if [ $key_len -gt 255 ]; then
    echo "E: length is greater than 255"
    false
    exit
fi

if ! [[ $key_first_char =~ ^[0-9a-zA-Z]+$ ]]; then
    echo "E: first character is not valid"
    false
    exit
fi

if ! [[ $string =~ ^[0-9a-zA-Z._-]+$ ]]; then
    echo "E: one of character is not valid"
    false
    exit
fi
