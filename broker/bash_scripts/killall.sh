#!/bin/bash

#if [ "$EUID" -ne 0 ]
#  then echo "Please run as root: sudo ./killall.sh"
#  exit
#fi

# sudo killall ipfs
# pkill -f <application_na>

GREEN='\033[0;32m'
NC='\033[0m' # No Color
kill -9 $(ps aux | grep -E "python.*[e]ndCode"      | awk '{print $2}') > /dev/null 2>&1
kill -9 $(ps aux | grep -E "python.*[s]tartCode"    | awk '{print $2}') > /dev/null 2>&1
kill -9 $(ps aux | grep -E "python.*[d]riverCancel" | awk '{print $2}') > /dev/null 2>&1
kill -9 $(ps aux | grep -E "python.*[D]river.py"    | awk '{print $2}') > /dev/null 2>&1

killall python3 2> /dev/null

squeue | tail -n+2 | awk '{print $1}' | xargs scancel 2> /dev/null

printf "killall for ebloc-broker test [ ${GREEN}SUCCESS${NC} ]\n"
