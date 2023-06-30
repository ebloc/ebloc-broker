#!/bin/bash

DIR=/var/ebloc-broker
if grep -q docker /proc/1/cgroup; then  # inside docker
    BASE_DIR=/workspace/ebloc-broker/broker
else
    BASE_DIR=~/ebloc-broker/broker
fi

FILE=$BASE_DIR/bash_scripts/slurm_mail_prog.sh
cp $FILE $DIR/
rm -f $DIR/slurm_mail_prog.sh.bak
line_old="_HOME"
line_new=$(echo $HOME | sed 's/\//\\\//g')
sed -i.bak "s/^\(_HOME=\).*/\1\"$line_new\"/" $DIR/slurm_mail_prog.sh
rm -f $DIR/slurm_mail_prog.sh.bak
