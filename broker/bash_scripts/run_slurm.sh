#!/bin/bash

MA="\033[33;35m"; RED="\033[1;31m"; GREEN="\033[1;32m"; PURPLE="\033[1;34m"; NC="\033[0m"
alias sudo='nocorrect sudo'
USER=$(whoami)
VERBOSE=true

run_worker_slurmd_nodes () {
    echo "#> running worker slurmd nodes"
    ## https://slurm.schedmd.com/faq.html#multi_slurmd
    IFS=/ read A  I O T <<<$(command sinfo -h -o%C)
    for id in $( seq 1 $T ); do
        echo "==> sudo slurmd -N "$(hostname -s)$id
        sudo slurmd -N $(hostname -s)$id &
    done
    # When starting the slurmd daemon, include the NodeName of the node that it is
    # supposed to serve on the execute line (e.g. "slurmd -N hostname").
    # sudo /usr/local/sbin/slurmd -N $(hostname -s)1
    # sudo /usr/local/sbin/slurmd -N $(hostname -s)2
    # sudo /usr/local/sbin/slurmd -N $(hostname -s)3
    # sudo /usr/local/sbin/slurmd -N $(hostname -s)4
    #
    # example:
    # sudo slurmd -N ocean2 -Dvvv
}

_kill () {
    if [[ $1 =~ ^[0-9]+$ ]]; then
        kill -9 $1;
    else
        if [[ $1 == "emacs" ]]; then
            strings=("emacsclient" "flake8" "pylint" "pylsp");
            for pattern in "${strings[@]}";
            do
                nocorrect sudo pkill -f -f "$pattern";
            done;
        fi;
        sudo kill -9 "$(ps auxww | grep -E "$1" | grep -v -e "grep" -e "emacsclient" | awk '{print $2}')" > /dev/null 2>&1;
    fi
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
    _kill "$i" > /dev/null 2>&1
    # sudo killall "$i" > /dev/null 2>&1
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
sudo -u $USER /usr/local/sbin/slurmctld -ic
sleep 1.0
run_worker_slurmd_nodes
squeue | tail -n+2 | awk '{print $1}' | xargs scancel 2> /dev/null
scontrol show node

dir=$(/usr/bin/pwd)
cd /home/"$(logname)"/ebloc-broker/broker/_slurm/example/
sbatch slurm_test.sh
cd $dir

echo ""
/usr/local/bin/sinfo -N -l

echo ""
ps auxww | grep -v -e grep -e emacsclient -e "/usr/bin/ps" -e "run_slurm.sh" | \
    grep -v unattended-upgrade-shutdown | \
    grep --color=auto --exclude-dir={.bzr,CVS,.git,.hg,.svn,.idea,.tox,.mypy_cache} -E "slurm";

echo ""
squeue



#: verbose
# sudo /usr/local/sbin/slurmctld -cDvvvvvv

# for i in {0..10..1}; do
#     echo "Welcome $i times"
# done
# sudo slurmd -N ocean2 -Dvvv
