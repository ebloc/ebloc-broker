#!/bin/bash

GREEN='\033[0;32m'; NC='\033[0m'
declare -a arr=("python.*[e]nd_code"
                "python.*[s]tart_code"
                "python.*[d]river_cancel"
                "python.*[e]blocbroker"
                "ipfs")
for i in "${arr[@]}"; do
    kill -9 $(ps auxww | grep -E "$i" | awk '{print $2}') > /dev/null 2>&1
done

killall python 2> /dev/null
killall python3 2> /dev/null

timeout 2 squeue && echo "## killall all jobs in squeue"
if [ $? -eq 0 ]; then
    squeue | tail -n+2 | awk '{print $1}' | ifne xargs scancel 2> /dev/null
fi
printf "kill for ebloc-broker test  [  ${GREEN}OK${NC}  ]\n"

#if [ "$EUID" -ne 0 ]
#  then echo "Please run as root: sudo ./killall.sh"
#  exit
#fi

# sudo killall ipfs
# pkill -f <application_na>
