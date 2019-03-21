#!/bin/bash

USER_ADDRESS=$1
BASEDIR=$2

## For testing
#USER_ADDRESS="dummy"
#BASEDIR="/var/eBlocBroker"

SLURMUSER="alper"
USERNAME=$(echo -n $USER_ADDRESS | md5sum | head -c-4) # Convert Ethereum User Address into 32-bits

# Force to add
sacctmgr remove user where user=$USERNAME --immediate
sacctmgr add account $USERNAME --immediate
sacctmgr create user $USERNAME defaultaccount=$USERNAME adminlevel=[None] --immediate    

if ! id -u $USERNAME > /dev/null 2>&1; then
    sudo useradd -d $BASEDIR/$USERNAME -m $USERNAME
    sudo mkdir $BASEDIR/$USERNAME/cache
    echo $USER_ADDRESS / $USERNAME 'is added as user.'
    
    sudo chmod 700 $BASEDIR/$USERNAME # Block others and people in the same group to do read/write/execute
    sudo setfacl -R -m user:$USERNAME:rwx  $BASEDIR/$USERNAME #Give read/write/execute access to USER1 on give folder.
    sudo setfacl -R -m user:$SLURMUSER:rwx $BASEDIR/$USERNAME #Give read/write/execute access to USER2 on give folder.
    
    sacctmgr add account $USERNAME --immediate
    sacctmgr create user $USERNAME defaultaccount=$USERNAME adminlevel=[None] --immediate    
else
    if [ ! -d $BASEDIR/$USERNAME ]; then
	# Control will enter here if $DIRECTORY doesn't exist.
	echo $BASEDIR/$USERNAME 'does not exist. Attempting to re-add the user.'
	
	sudo userdel $USERNAME
	sudo useradd -d $BASEDIR/$USERNAME -m $USERNAME
	sudo mkdir $BASEDIR/$USERNAME/cache

	sudo chmod 700 $BASEDIR/$USERNAME # Block others and people in the same group to do read/write/execute
	sudo setfacl -R -m user:$USERNAME:rwx  $BASEDIR/$USERNAME #Give read/write/execute access to USER1 on give folder.
	sudo setfacl -R -m user:$SLURMUSER:rwx $BASEDIR/$USERNAME #Give read/write/execute access to USER2 on give folder.

	echo $USER_ADDRESS / $USERNAME 'is created.'

	# Force to add
	sacctmgr remove user where user=$USERNAME --immediate
	sacctmgr add account $USERNAME --immediate
	sacctmgr create user $USERNAME defaultaccount=$USERNAME adminlevel=[None] --immediate    
    else
	echo $USER_ADDRESS / $USERNAME 'is already created.'
    fi
fi

# For test purposes:-------------------
# sudo userdel $USERNAME
# sudo rm -rf $BASEDIR/$USERNAME
# sacctmgr remove user where user=$USERNAME --immediate
# -------------------------------------
