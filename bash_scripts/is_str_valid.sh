#!/bin/bash

string=$1
key_first_char=$(echo $string | cut -c1-1)
if ! [[ $key_first_char =~ ^[0-9a-zA-Z]+$ ]]; then
    echo "E: fist character is not valid"
    false
    exit
fi

if ! [[ $string =~ ^[0-9a-zA-Z._-]+$ ]]; then
    echo "E: one of character is not valid"
    false
    exit
fi


key_len=$(echo "${#string}")
if [ $key_len -gt 255 ]; then
    echo "E: length is greater than 255"
    false
    exit
fi
