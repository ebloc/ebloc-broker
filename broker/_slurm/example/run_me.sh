#!/bin/bash

dir=$(/usr/bin/pwd)
is_internet () {
    output=$(ping -c 1 -q google.com >&/dev/null; echo $?)
    if [ $output -eq 0 ]
    then
        echo "connected"
        return 0
    else
        echo "not_connected"
        return 1
    fi
}

is_internet
echo is_internet=$(is_internet) >> $dir/completed.txt
echo $dir >> $dir/completed.txt
g++ helloworld.cpp -o hello
./hello
sleep 10
