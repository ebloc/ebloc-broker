#!/bin/bash

function error_with_msg {
    if [[ "$count" -eq 0 ]]; then
        echo
        echo >&2 "$1"
        exit 1
    fi
}

function check_running_status {
    for count in {2..0}; do
        STATUS=$(/usr/bin/supervisorctl status $1 | awk '{print $2}')
        echo "#> $1 is in the $STATUS state."
        if [[ "$STATUS" = "RUNNING" ]]; then
            break
        else
            sleep 1
        fi
    done
}

function check_port_status {
    for count in {2..0}; do
        echo 2>/dev/null >/dev/tcp/localhost/$1
        if [[ "$?" -eq 0 ]]; then
            echo "#> port $1 is listening"
            break
        else
            echo "#> port $1 is not listening"
            sleep 1
        fi
    done
}

function start_service {
    echo "## Starting $1"
    /usr/bin/supervisorctl start $1
    check_running_status $1
}

function check_cluster () {
    echo "==> waiting for the cluster to become available"
    for count in {10..0}; do
        if ! grep -E "up.*idle" <(timeout 1 sinfo); then
            sleep 1
        else
            break
        fi
    done
    error_with_msg "E: slurm partitions failed to start"
}

if [ ! -d "/var/lib/mysql/mysql" ]; then
    echo "[mysqld]\nskip-host-cache\nskip-name-resolve" > /etc/my.cnf.d/docker.cnf
    echo "#> Initializing database"
    /usr/bin/mysql_install_db --user=mysql &> /dev/null
    echo "#> Database initialized  [  OK  ]"
fi

if [ ! -d "/var/lib/mysql/slurm_acct_db" ]; then
    /usr/bin/mysqld_safe &
    for count in {30..0}; do
        if echo "SELECT 1" | mysql &> /dev/null
        then
            break
        fi
        echo "## starting MariaDB to create Slurm account database"
        sleep 1
    done
    error_with_msg "MariaDB did not start"
    echo "* Creating Slurm acct database"
    mysql -NBe "CREATE USER 'slurm'@'localhost' identified by 'password'"
    mysql -NBe "GRANT ALL ON slurm_acct_db.* to 'slurm'@'localhost' identified by 'password' with GRANT option"
    mysql -NBe "GRANT ALL ON slurm_acct_db.* to 'slurm'@'slurmctl' identified by 'password' with GRANT option"
    mysql -NBe "CREATE DATABASE slurm_acct_db"
    echo "#> Slurm acct database created. Stopping MariaDB"
    pkill -f mysqld
    for count in {10..0}; do
        if echo "SELECT 1" | mysql &> /dev/null
        then
            sleep 1
        else
            break
        fi
    done
    error_with_msg "MariaDB did not stop"
fi

echo "#> starting supervisord process manager"
/usr/bin/supervisord --configuration /etc/supervisord.conf

# order of the programs is important
sudo chown munge:munge -R /run/munge  # double check
nohup sudo -u munge munged -F > /var/log/munged.log &!
# munged: Info: Unauthorized credential for client UID=0 GID=0 // but works

for service in mysqld slurmdbd slurmctld slurmd_1 slurmd_2 mongod ipfs; do
    start_service $service
done

# for port in 6817 6818 6819 6001 6002; do
#     check_port_status $port
# done

# check_cluster
/usr/bin/supervisorctl start startup >/dev/null 2>&1
echo "#> cluster is now available"
exec "$@"
