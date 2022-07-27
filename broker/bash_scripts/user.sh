#!/bin/bash

USERADDRESS=$1
BASEDIR=$2
SLURMUSER=$3

force_add_slurm_user () {  # force to re-add slurm user
    sacctmgr remove user where user=$_USERNAME --immediate
    sacctmgr add account $_USERNAME --immediate
    sacctmgr create user $_USERNAME defaultaccount=$_USERNAME adminlevel=[None] --immediate
}

# For testing
## USERADDRESS="dummy"
## BASEDIR="/var/eBlocBroker"
## SLURMUSER="netlab"

_USERNAME=$(echo -n $USERADDRESS | md5sum | head -c-4)  # convert Ethereum User Address into 32-bits
if ! id -u $_USERNAME > /dev/null 2>&1; then
    sudo useradd -d $BASEDIR/$_USERNAME -m $_USERNAME
    sudo mkdir -p $BASEDIR/$_USERNAME/cache
    echo $USERADDRESS / $_USERNAME 'is added as user'

    # sudo iptables -A OUTPUT -m owner --uid-owner $_USERNAME -j DROP
    sudo chmod 700 $BASEDIR/$_USERNAME  # block others and people in the same group to do read/write/execute
    sudo setfacl -R -m user:$_USERNAME:rwx  $BASEDIR/$_USERNAME  # give Read/Write/Execute access to USER on the give folder
    sudo setfacl -R -m user:$SLURMUSER:rwx $BASEDIR/$_USERNAME  # give Read/Write/Execute access to root user on the give folder

    # add user to slurm
    sacctmgr remove user where user=$_USERNAME --immediate
    sacctmgr add account $_USERNAME --immediate
    sacctmgr create user $_USERNAME defaultaccount=$_USERNAME adminlevel=[None] --immediate
else
    if [ ! -d $BASEDIR/$_USERNAME ]; then
        # control will enter here if $DIRECTORY doesn't exist
        echo $BASEDIR/$_USERNAME 'does not exist. Attempting to re-add the user'

        sudo userdel $_USERNAME
        sudo useradd -d $BASEDIR/$_USERNAME -m $_USERNAME
        sudo mkdir -p $BASEDIR/$_USERNAME/cache

        # sudo iptables -A OUTPUT -m owner --uid-owner $_USERNAME -j DROP
        sudo chmod 700 $BASEDIR/$_USERNAME  # block others and people in the same group to do read/write/execute
        sudo setfacl -R -m user:$_USERNAME:rwx  $BASEDIR/$_USERNAME  # give Read/Write/Execute access to USER on the give folder
        sudo setfacl -R -m user:$SLURMUSER:rwx $BASEDIR/$_USERNAME  # give Read/Write/Execute access to root user on the give folder

        echo $USERADDRESS / $_USERNAME 'is created'
        ## force to add user to slurm
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
# sudo rm -rf $BASEDIR/$_USERNAME
# sacctmgr remove user where user=$_USERNAME --immediate
