#!/bin/bash

USER_ADDRESS=$1 # "0x75a4c787c5c18c587b284a904165ff06"
BASEDIR=$2;

USERNAME=$(echo -n $USER_ADDRESS | md5sum | head -c-4); # Convert Ethereum User Address into 32-bits

sudo userdel $USERNAME
sudo rm -rf $BASEDIR/USERS/$USERNAME

if ! id -u $USERNAME > /dev/null 2>&1; then
    sudo useradd -m -d $BASEDIR/USERS/$USERNAME $USERNAME;
    echo $USER_ADDRESS / $USERNAME 'is added as user.';
    sudo chown alper $BASEDIR/USERS/$USERNAME
else
    echo $USER_ADDRESS / $USERNAME 'is already created.';
fi

