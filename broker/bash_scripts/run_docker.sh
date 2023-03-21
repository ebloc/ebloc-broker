#!/bin/bash

# nohup ./run_docker.sh &
# tail -f docker.log

while true
do
    output=$(docker ps | grep 7440c08d3dd5)
    if [[ -z "$output" ]]; then
        echo "Docker crashed... restarting"
        nohup docker-compose -f bootnode.yml up >> docker.log 2>&1 &!
    fi
    echo -n "OK     " $(date)
    echo -n -e "\e[0K\r"
    # echo -e "\\rOK"
    sleep 2
done
