#!/bin/bash

RED="\033[1;31m"; GREEN='\033[0;32m'; NC='\033[0m'
countdown () {
   date1=$((`date +%s` + $(expr $1 - 1)))
   while [ "$date1" -ge `date +%s` ]; do
     echo -ne "$(date -u --date @$(($date1 - `date +%s`)) +%H:%M:%S)\r"
     sleep 0.1
   done
}

num=$(ps axuww | grep -E "[h]ypercorn app_ebb:app" | \
          grep -v -e "grep" -e "emacsclient" -e "flycheck_" | wc -l)
if [ $num -ge 1 ]; then
    echo "warning: app_ebb is already running"
    exit
fi

while true; do
    clear -x
    hypercorn app_ebb:app -b 127.0.0.1:8000 --reload
    echo -e "${GREEN}-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-${NC}"
    echo "countdown for 30 seconds  "
    countdown 30
    echo "[  ${GREEN}OK${NC}  ]"
done
