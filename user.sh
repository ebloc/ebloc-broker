#!/bin/bash

USER_ADDRESS=$1 # "0x75a4c787c5c18c587b284a904165ff06"
BASEDIR=$2;     # /var/eBlocBroker

USERNAME=$(echo -n $USER_ADDRESS | md5sum | head -c-4); # Convert Ethereum User Address into 32-bits
SLURMUSER='alper';

# For test purposes:-------------------
# sudo userdel $USERNAME
# sudo rm -rf $BASEDIR/$USERNAME
# sacctmgr remove user where user=$USERNAME --immediate
# -------------------------------

if ! id -u $USERNAME > /dev/null 2>&1; then
    sudo useradd -d $BASEDIR/$USERNAME -m $USERNAME;
    echo $USER_ADDRESS / $USERNAME 'is added as user.';
    
    sudo chmod 700 $BASEDIR/$USERNAME # Block others and people in the same group to do read/write/execute
    sudo setfacl -R -m user:$MAINUSER:rwx  $BASEDIR/$USERNAME
    sudo setfacl -R -m user:$SLURMUSER:rwx $BASEDIR/$USERNAME
    
    sacctmgr add account $USERNAME --immediate
    sacctmgr create user $USERNAME defaultaccount=$USERNAME adminlevel=[None] --immediate    
else
    echo $USER_ADDRESS / $USERNAME 'is already created.';
fi
