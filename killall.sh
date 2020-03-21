#!/bin/bash
#                              |
# To Run:  sudo bash killall.sh|
#-------------------------------

#if [ "$EUID" -ne 0 ]
#  then echo "Please run as root: sudo ./killall.sh"
#  exit
#fi

# sudo killall ipfs
# pkill -f <application_na>

ps aux | grep -E "python.*[e]ndCode"      | awk '{print $2}' | xargs kill -9 $1 2> /dev/null
ps aux | grep -E "python.*[s]tartCode"    | awk '{print $2}' | xargs kill -9 $1 2> /dev/null
ps aux | grep -E "python.*[d]riverCancel" | awk '{print $2}' | xargs kill -9 $1 2> /dev/null
ps aux | grep -E "python.*[D]river.py"    | awk '{print $2}' | xargs kill -9 $1 2> /dev/null
killall python3 2> /dev/null

squeue | tail -n+2 | awk '{print $1}' | xargs scancel $1 2> /dev/null

echo 'Killall is done.'
