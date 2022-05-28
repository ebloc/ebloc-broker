#!/bin/bash

#if [ "$EUID" -ne 0 ]
#  then echo "Please run as root: sudo ./killall.sh"
#  exit
#fi

# sudo killall ipfs
# pkill -f <application_na>

GREEN='\033[0;32m'; NC='\033[0m'
kill -9 $(ps auxww | grep -E "python.*[e]nd_code"      | awk '{print $2}') > /dev/null 2>&1
kill -9 $(ps auxww | grep -E "python.*[s]tart_code"    | awk '{print $2}') > /dev/null 2>&1
kill -9 $(ps auxww | grep -E "python.*[d]river_cancel" | awk '{print $2}') > /dev/null 2>&1
kill -9 $(ps auxww | grep -E "python.*[e]blocbroker"   | awk '{print $2}') > /dev/null 2>&1
kill -9 $(ps auxww | grep -E "ipfs"                    | awk '{print $2}') > /dev/null 2>&1

killall python 2> /dev/null
killall python3 2> /dev/null
echo "## killall all jobs in squeue"
squeue | tail -n+2 | awk '{print $1}' | xargs scancel 2> /dev/null
printf "killall for ebloc-broker test  [  ${GREEN}OK${NC} ]\n"
