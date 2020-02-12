#!/bin/bash
#                              |
# To Run:  sudo bash killall.sh|
#-------------------------------

if [ "$EUID" -ne 0 ]
  then echo "Please run as root: sudo ./killall.sh"
  exit
fi

# sudo killall ipfs
# pkill -f <application_na>

ps aux | grep "[e]ndCode"      | awk '{print $2}' | xargs kill -9 $1 2> /dev/null
ps aux | grep "[s]tartCode"    | awk '{print $2}' | xargs kill -9 $1 2> /dev/null
ps aux | grep "[d]riverCancel" | awk '{print $2}' | xargs kill -9 $1 2> /dev/null
ps aux | grep "[D]river.py"    | awk '{print $2}' | xargs kill -9 $1 2> /dev/null
killall python3

squeue | tail -n+2 | awk '{print $1}' | xargs scancel $1 2> /dev/null

echo 'Killall is done.'
