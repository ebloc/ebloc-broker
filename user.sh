#!/bin/bash

USERADDRESS=$1
BASEDIR=$2
SLURMUSER=$3

# For testing
## USERADDRESS="dummy"
## BASEDIR="/var/eBlocBroker"
## SLURMUSER="netlab"

USERNAME=$(echo -n $USERADDRESS | md5sum | head -c-4)  # Convert Ethereum User Address into 32-bits

## Force to add
#sacctmgr remove user where user=$USERNAME --immediate
#sacctmgr add account $USERNAME --immediate
#sacctmgr create user $USERNAME defaultaccount=$USERNAME adminlevel=[None] --immediate

if ! id -u $USERNAME > /dev/null 2>&1; then
    sudo useradd -d $BASEDIR/$USERNAME -m $USERNAME
    sudo mkdir -p $BASEDIR/$USERNAME/cache
    echo $USERADDRESS / $USERNAME 'is added as user.'

    sudo chmod 700 $BASEDIR/$USERNAME # Block others and people in the same group to do read/write/execute
    sudo setfacl -R -m user:$USERNAME:rwx  $BASEDIR/$USERNAME #Give Read/Write/Execute access to USER on the give folder.
    sudo setfacl -R -m user:$SLURMUSER:rwx $BASEDIR/$USERNAME #Give Read/Write/Execute access to root user on the give folder.

    # Add user to Slurm
    sacctmgr remove user where user=$USERNAME --immediate
    sacctmgr add account $USERNAME --immediate
    sacctmgr create user $USERNAME defaultaccount=$USERNAME adminlevel=[None] --immediate
else
    if [ ! -d $BASEDIR/$USERNAME ]; then
	# Control will enter here if $DIRECTORY doesn't exist.
	echo $BASEDIR/$USERNAME 'does not exist. Attempting to re-add the user.'

	sudo userdel $USERNAME
	sudo useradd -d $BASEDIR/$USERNAME -m $USERNAME
	sudo mkdir -p $BASEDIR/$USERNAME/cache

	sudo chmod 700 $BASEDIR/$USERNAME # Block others and people in the same group to do read/write/execute
	sudo setfacl -R -m user:$USERNAME:rwx  $BASEDIR/$USERNAME # Give Read/Write/Execute access to USER on the give folder.
	sudo setfacl -R -m user:$SLURMUSER:rwx $BASEDIR/$USERNAME # Give Read/Write/Execute access to root user on the give folder.

	echo $USERADDRESS / $USERNAME 'is created.'

	## Force to add user to Slurm
	sacctmgr remove user where user=$USERNAME --immediate
	sacctmgr add account $USERNAME --immediate
	sacctmgr create user $USERNAME defaultaccount=$USERNAME adminlevel=[None] --immediate
    else
	echo $USERADDRESS / $USERNAME 'has already been created.'
    fi
fi

# For test purposes:-------------------
# sudo userdel $USERNAME
# sudo rm -rf $BASEDIR/$USERNAME
# sacctmgr remove user where user=$USERNAME --immediate
# -------------------------------------
