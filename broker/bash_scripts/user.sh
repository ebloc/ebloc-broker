#!/bin/bash

USERADDRESS=$1
BASEDIR=$2
SLURMUSER=$3

#: for testing
# USERADDRESS="dummy"
# BASEDIR="/var/ebloc-broker"
# SLURMUSER="slurm"

force_add_slurm_user () {  # force to re-add slurm user
    sacctmgr remove user where user=$_USERNAME --immediate
    sacctmgr add account $_USERNAME --immediate
    sacctmgr create user $_USERNAME defaultaccount=$_USERNAME adminlevel=[None] --immediate
}

_USERNAME=$(echo -n $USERADDRESS | md5sum | head -c-4)  # convert ethereum user address into 32-bits
USER_HOME_DIR=$BASEDIR/$_USERNAME
if ! id -u $_USERNAME > /dev/null 2>&1; then
    sudo useradd -d $USER_HOME_DIR -m $_USERNAME
    sudo mkdir -p $USER_HOME_DIR/cache
    echo $USERADDRESS / $_USERNAME 'is added as user'

    # sudo iptables -A OUTPUT -m owner --uid-owner $_USERNAME -j DROP
    USER_HOME_DIR=$USER_HOME_DIR
    sudo chmod 700 $USER_HOME_DIR  # block others and people in the same group to do read/write/execute
    sudo setfacl -R -m user:$_USERNAME:rwx $USER_HOME_DIR  # give read/write/execute access to USER on the given folder
    sudo setfacl -R -m user:$SLURMUSER:rwx $USER_HOME_DIR  # give read/write/execute access to the root slurm user on the given folder

    # add user to slurm
    sacctmgr remove user where user=$_USERNAME --immediate
    sacctmgr add account $_USERNAME --immediate
    sacctmgr create user $_USERNAME defaultaccount=$_USERNAME adminlevel=[None] --immediate
else
    if [ ! -d $USER_HOME_DIR ]; then
        # control will enter here if $DIRECTORY doesn't exist
        echo $USER_HOME_DIR 'does not exist. Attempting to re-add the user'

        sudo userdel $_USERNAME
        sudo useradd -d $USER_HOME_DIR -m $_USERNAME
        sudo mkdir -p $USER_HOME_DIR/cache

        # sudo iptables -A OUTPUT -m owner --uid-owner $_USERNAME -j DROP
        sudo chmod 700 $USER_HOME_DIR  # block others and people in the same group to do read/write/execute
        sudo setfacl -R -m user:$_USERNAME:rwx $USER_HOME_DIR  # give read/write/execute access to USER on the given folder
        sudo setfacl -R -m user:$SLURMUSER:rwx $USER_HOME_DIR  # give read/write/execute access to root user on the given folder

        echo $USERADDRESS / $_USERNAME 'is created'
        #: force to add user to slurm
        sacctmgr remove user where user=$_USERNAME --immediate
        sacctmgr add account $_USERNAME --immediate
        sacctmgr create user $_USERNAME defaultaccount=$_USERNAME adminlevel=[None] --immediate
    else
        echo $USERADDRESS / $_USERNAME 'has already been created'
    fi
fi

# For test purposes
# =================
# sudo userdel $_USERNAME
# sudo rm -rf $USER_HOME_DIR
# sacctmgr remove user where user=$_USERNAME --immediate
