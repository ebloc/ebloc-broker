#!/bin/bash

TMP_DIR=$HOME/.ebloc-broker
configure_coinbase () { # coinbase address setup
    COINBASE=$(echo $COINBASE)
    if [[ ! -v COINBASE ]]; then
        echo "COINBASE is not set"
        echo "Type your provider Ethereum Address, followed by [ENTER]:"
        read COINBASE
        echo 'export COINBASE="'$COINBASE'"' >> $HOME/.profile
    elif [[ -z "$COINBASE" ]]; then
        echo "COINBASE is set to the empty string"
        echo "Type your provider Ethereum Address, followed by [ENTER]:"
        read COINBASE
        echo 'export COINBASE="'$COINBASE'"' >> $HOME/.profile
    else
        echo "COINBASE is: $COINBASE"
        check=$(eblocbroker/is_address.py $COINBASE)
        if [ "$check" != "True" ]; then
            echo "Ethereum address is not valid, please use a valid one."
            exit
        fi
        sed -i.bak "s/^\(PROVIDER_ID=\).*/\1\"$COINBASE\"/" $TMP_DIR/.env
        rm $TMP_DIR/.env.bak
    fi
}

configure_oc () { # OC_USER address setup
    OC_USER=$(echo $OC_USER)
    if [[ ! -v OC_USER ]]; then
        echo "OC_USER is not set"
        echo "Type your OC_USER, followed by [ENTER]:"
        read OC_USER
    elif [[ -z "$OC_USER" ]]; then
        echo "OC_USER is set to the empty string"
        echo "Type your OC_USER, followed by [ENTER]:"
        read OC_USER
    fi
    sed -i.bak "s/^\(OC_USER=\).*/\1\"$OC_USER\"/" $TMP_DIR/.env
    rm -f $TMP_DIR/.env.bak

    if ! grep -q "export OC_USER=" $HOME/.profile; then
        echo 'export OC_USER="'$OC_USER'"' >> $HOME/.profile
    fi
    source $HOME/.profile
}

configure_slurm () { # slurm setup
    sudo killall slurmctld slurmdbd slurmd
    var=$(echo $current_dir | sed 's/\//\\\//g')
    var=$var"/bash_scripts"
    # With JobRequeue=0 or --no-requeue,
    # the job will not restart automatically, please see https://stackoverflow.com/a/43366542/2402577
    sudo sed -i.bak "s/^\(.*JobRequeue=\).*/\10/" /usr/local/etc/slurm.conf
    sudo rm -f /usr/local/etc/slurm.conf.bak

    sudo sed -i.bak "s/^\(MailProg=\).*/\1$var\/slurmScript.sh/" /usr/local/etc/slurm.conf
    sudo rm -f /usr/local/etc/slurm.conf.bak

    # MinJobAge assingned to '1' day,
    # The minimum age of a completed job before its record is purged from Slurm's active database.
    sudo sed -i.bak "s/^\(.*MinJobAge=\).*/\186400/" /usr/local/etc/slurm.conf
    sudo rm /usr/local/etc/slurm.conf.bak
    grep "MailProg" /usr/local/etc/slurm.conf
}

configure_ipfs () { # ipfs setups
    l=$(logname)
    sudo chown -R "$l:$l" $HOME/.ipfs/
    sudo mkdir -p /ipfs
    sudo mkdir -p /ipns
    sudo chown $l:root /ipfs
    sudo chown $l:root /ipns
}

current_dir=$HOME/ebloc-broker

# Folder Setup
# ============
DIR=/var/ebloc-broker
mkdir -p $DIR/cache
if [ ! -d $DIR ]; then
    sudo mkdir -p $DIR
    sudo chown $(whoami) -R $DIR
fi

if [ ! -d $TMP_DIR ]; then
    mkdir -p $TMP_DIR
fi

touch $TMP_DIR/config.yaml
mkdir -p $TMP_DIR/private
mkdir -p $TMP_DIR/drivers_output
mkdir -p $TMP_DIR/links
mkdir -p $TMP_DIR/transactions
mkdir -p $TMP_DIR/end_code_output

if [ ! -f $TMP_DIR/.env ]; then
    cp $current_dir/.env $TMP_DIR
fi

# EBLOCPATH
# =========
venvPath=$HOME"/venv"
var=$(echo $venvPath | sed 's/\//\\\//g')
sed -i.bak "s/^\(VENV_PATH=\).*/\1\"$var\"/" $HOME/ebloc-broker/broker/bash_scripts/slurmScript.sh
rm $HOME/ebloc-broker/broker/bash_scripts/slurmScript.sh.bak

# LOG_PATH
# ========
lineNew=$TMP_DIR
var=$(echo $lineNew | sed 's/\//\\\//g')
sed -i.bak "s/^\(LOG_PATH=\).*/\1\"$var\"/" $TMP_DIR/.env
rm -f $TMP_DIR/.env.bak

# GDRIVE
# ======
FILE=$HOME/.gdrive
if [ -f "$FILE" ]; then
    sudo chown $(whoami) -R $HOME/.gdrive
fi

lineNew=$(which gdrive | sed 's/\//\\\//g')
sed -i.bak "s/^\(GDRIVE=\).*/\1\"$lineNew\"/" $TMP_DIR/.env
rm -f $TMP_DIR/.env.bak

# EBLOCPATH
# =========
eblocbrokerPath="$HOME/ebloc-broker"
var=$(echo $eblocbrokerPath | sed 's/\//\\\//g')
sed -i.bak "s/^\(EBLOCPATH=\).*/\1\"$var\"/" $TMP_DIR/.env
rm $TMP_DIR/.env.bak

# User Name
# =========
lineOld="whoami"
lineNew=$(logname)

sed -i.bak "s/^\(WHOAMI=\).*/\1\"$lineNew\"/" $TMP_DIR/.env
rm -f $TMP_DIR/.env.bak

# RPC PORT
# ========
lineOld="8545"
sed -i.bak "s/^\(RPC_PORT=\).*/\1$lineOld/" $TMP_DIR/.env
rm $TMP_DIR/.env.bak

# PATH Name
# =========
lineOld="EBLOCBROKER_PATH"
lineNew=$(echo $current_dir | sed 's/\//\\\//g')

sed -i.bak 's/'$lineOld'/'$lineNew'/' $TMP_DIR/.env
rm -f $TMP_DIR/.env.bak

sed -i.bak "s/^\(EBLOCBROKER_PATH=\).*/\1\"$lineNew\"/" $HOME/ebloc-broker/broker/bash_scripts/slurmScript.sh
rm -f $HOME/ebloc-broker/broker/bash_scripts/slurmScript.sh.bak

# configure_coinbase
# configure_oc
# configure_ipfs
## configure_slurm

echo -e "Note: Update the following file "$TMP_DIR"/.eudat_provider.txt' with
your EUDAT account's password. Best to make sure the file is not readable or
even listable for anyone but you. You achieve this with: 'chmod 700
eudat_password.txt'"

## Setup
## sudo ln -s /usr/bin/node /usr/local/bin/node
# sudo chmod 700 /home/*
