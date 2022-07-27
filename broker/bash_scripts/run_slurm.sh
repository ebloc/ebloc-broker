#!/bin/bash

MA="\033[33;35m"; RED="\033[1;31m"; GREEN="\033[1;32m"; PURPLE="\033[1;34m"; NC="\033[0m"
verbose=false
alias sudo='nocorrect sudo'
USER=$(whoami)

run_worker_slurmd_nodes () {
    echo "#> Running worker slurmd nodes"
    ## https://slurm.schedmd.com/faq.html#multi_slurmd
    IFS=/ read A  I O T <<<$(sinfo -h -o%C)
    echo $T
    for i in $( seq 0 $T ); do
        id=$((i+1))  # 2.3.4....
        sudo slurmd -N $(hostname -s)$id &
    done
    # When starting the slurmd daemon, include the NodeName of the node that it is
    # supposed to serve on the execute line (e.g. "slurmd -N hostname").
    # sudo /usr/local/sbin/slurmd -N <hostname>1
    # sudo /usr/local/sbin/slurmd -N <hostname>2
    # sudo /usr/local/sbin/slurmd -N <hostname>3
    # sudo /usr/local/sbin/slurmd -N <hostname>4
    # sudo slurmd -N ocean2 -Dvvv
}

if [[ $(whoami) == "root" ]] ; then
    echo -e "$PURPLE##$NC logname=$MA"$(logname)$NC
    echo -e "$PURPLE##$NC hostname=$MA"$(hostname -s)$NC
    USER=$(logname)
fi

sudo /etc/init.d/mysql start
sudo systemctl --no-pager status mysql

declare -a arr=("slurmd" "slurmdbd" "slurmctld")
for i in "${arr[@]}"; do  # https://stackoverflow.com/a/8880633/2402577
    sudo killall "$i" > /dev/null 2>&1
done

sudo rm -f /var/run/slurmdbd.pid
sudo chown $USER /var/run/slurmctld.pid 2>/dev/null
sudo chown $USER -R /var/log/slurm/
DIR="$( cd "$( dirname "$0" )" && pwd )"
sudo $DIR/run_munge.sh
sudo /usr/local/sbin/slurmd

# sudo /usr/local/sbin/slurmd -N $(hostname -s)  # emulate mode
sudo chown mysql:mysql -R /var/lib/mysql
sudo slurmdbd &
sleep 2.0
sudo -u $USER mkdir -p /tmp/slurmstate
sudo chown -R $USER /tmp/slurmstate
# sudo systemctl --no-pager status --full systemd-journald
if [ "$verbose" = true ] ; then
    sudo /usr/local/sbin/slurmctld -cDvvvvvv
    # sudo -u $(logname) /usr/local/sbin/slurmctld -cDvvvvvv
else
    sudo -u $USER /usr/local/sbin/slurmctld -c
    sleep 1.0
    run_worker_slurmd_nodes
    squeue | tail -n+2 | awk '{print $1}' | xargs scancel 2> /dev/null
    scontrol show node
    echo ""
    /usr/local/bin/sinfo -N -l
fi

# for i in {0..10..1}; do
#     echo "Welcome $i times"
# done
# sudo slurmd -N ocean2 -Dvvv
