#!/bin/bash

function check_running_status {
    for count in {2..0}; do
        STATUS=$(/usr/bin/supervisorctl status $1 | awk '{print $2}')
        echo "#> $1 is in the $STATUS state."
        if [[ "$STATUS" = "RUNNING" ]]
        then
            break
        else
            sleep 1
        fi
    done
}

function start_service {
    echo "## Starting $1"
    /usr/bin/supervisorctl start $1
    check_running_status $1
}

echo "#> Starting supervisord process manager"
/usr/bin/supervisord --configuration /etc/supervisord.conf
for service in mongod_r ipfsd
do
    start_service $service
done
exec "$@"
