#!/bin/bash

dir=$(/usr/bin/pwd)
is_internet ()
{
    wget -q --tries=10 --timeout=20 --spider http://google.com;
    if [[ $? -eq 0 ]]; then
        echo "connected"
        return 0
    else
        echo "not_connected"
        return 1
    fi
}
is_internet
whoami
echo is_internet=$(is_internet) >> $dir/completed.txt
echo $dir >> $dir/completed.txt
g++ helloworld.cpp -o hello
./hello
printf "sleeping... "
sleep 20
echo "[ok]"
