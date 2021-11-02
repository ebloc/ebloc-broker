#!/bin/bash

echo "==> logname="$(logname)
_LOGNAME=$(whoami)
if [[ $(whoami) == "root" ]] ; then
    _LOGNAME="alper"
fi
sudo killall slurmd slurmdbd slurmctld > /dev/null 2>&1
DIR="$( cd "$( dirname "$0" )" && pwd )"
sudo $DIR/run_munge.sh
sudo /usr/local/sbin/slurmd
sudo /usr/local/sbin/slurmdbd &
sleep 1.0
sudo -u $_LOGNAME mkdir -p /tmp/slurmstate
sudo chown -R $_LOGNAME /tmp/slurmstate
sudo -u $_LOGNAME /usr/local/sbin/slurmctld # -cDvvvvvv
# sudo -u $(logname) /usr/local/sbin/slurmctld # -cDvvvvvv
sleep 1.0
/usr/local/bin/sinfo
