#!/bin/bash

GREEN="\033[1;32m"; NC="\033[0m"
LOG_DIR=~/.ebloc-broker
BASE_DIR=~/ebloc-broker/broker
DIR=/var/ebloc-broker

yes_or_no () {
    while true; do
        string="$GREEN#>$NC $* [Y/n]:"
        read -p "$(echo -e $string) " yn
        case $yn in
            [Yy]*) return 0  ;;
            [Nn]*) echo "end" ; return  1 ;;
            * ) echo "Please answer yes or no";;
        esac
    done
}

set_email () {
    echo "Type your email-address, followed by [ENTER]:"
    read EMAIL
    line_old="EMAIL="
    line_new=$EMAIL
    sed -i.bak "s/^\(EMAIL=\).*/\1\"$line_new\"/" $DIR/slurm_mail_prog.sh
    rm -f $DIR/slurm_mail_prog.sh.bak

}

provider_setup () {
    ## configure_slurm
    _FILE=$DIR/slurm_mail_prog.sh
    FILE=$BASE_DIR/bash_scripts/slurm_mail_prog.sh
    EMAIL=$(cat ~/.ebloc-broker/cfg.yaml | shyaml get-value cfg.gmail)
    # [ ! -f $_FILE ] && cp $FILE $DIR/
    cp $FILE $DIR/
    line_old="EMAIL="
    line_new=$EMAIL
    sed -i.bak "s/^\(EMAIL=\).*/\1\"$line_new\"/" $DIR/slurm_mail_prog.sh
    rm -f $DIR/slurm_mail_prog.sh.bak
    line_old="_HOME"
    line_new=$(echo $HOME | sed 's/\//\\\//g')
    sed -i.bak "s/^\(_HOME=\).*/\1\"$line_new\"/" $DIR/slurm_mail_prog.sh
    rm -f $DIR/slurm_mail_prog.sh.bak
    # venv_path=$HOME"/venv"
    # var=$(echo $venv_path | sed 's/\//\\\//g')
    # sed -i.bak "s/^\(VENV_PATH=\).*/\1\"$var\"/" $DIR/slurm_mail_prog.sh
    # rm $DIR/slurm_mail_prog.sh.bak
    yes_or_no "Do you want to change your email" $EMAIL && set_email
}

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
        check=$($BASE_DIR/eblocbroker_scripts/is_address.py $COINBASE)
        if [ "$check" != "True" ]; then
            echo "Ethereum address is not valid, please use a valid one."
            exit
        fi
        # sed -i.bak "s/^\(PROVIDER_ID=\).*/\1\"$COINBASE\"/" $LOG_DIR/.env
        # rm $LOG_DIR/.env.bak
    fi
}

configure_oc () {  # OC_USER address setup
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
    # sed -i.bak "s/^\(OC_USER=\).*/\1\"$OC_USER\"/" $LOG_DIR/.env
    # rm -f $LOG_DIR/.env.bak

    if ! grep -q "export OC_USER=" $HOME/.profile; then
        echo 'export OC_USER="'$OC_USER'"' >> $HOME/.profile
    fi
    source $HOME/.profile
}

configure_slurm () { # slurm setup
    sudo killall slurmctld slurmdbd slurmd
    var=$(echo $LOG_DIR/slurm_mail_prog.sh | sed 's/\//\\\//g')
    # var=$var"/bash_scripts"
    # With JobRequeue=0 or --no-requeue,
    # the job will not restart automatically, please see https://stackoverflow.com/a/43366542/2402577
    sudo sed -i.bak "s/^\(.*JobRequeue=\).*/\10/" /usr/local/etc/slurm.conf
    sudo rm -f /usr/local/etc/slurm.conf.bak
    sudo sed -i.bak "s/^\(MailProg=\).*/\1$var/" /usr/local/etc/slurm.conf
    sudo rm -f /usr/local/etc/slurm.conf.bak
    # MinJobAge assingned to '1' day,
    # The minimum age of a completed job before its record is purged from Slurm's active database.
    sudo sed -i.bak "s/^\(.*MinJobAge=\).*/\172800/" /usr/local/etc/slurm.conf
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

# Folder Setup
# ============
if [ ! -d $DIR ]; then
    sudo mkdir -p $DIR
    sudo chown $(whoami) -R $DIR
fi
mkdir -p $DIR/cache

if [ ! -d $LOG_DIR ]; then
    mkdir -p $LOG_DIR
fi

touch $LOG_DIR/config.yaml
mkdir -p $LOG_DIR/private
mkdir -p $LOG_DIR/drivers_output
mkdir -p $LOG_DIR/links
mkdir -p $LOG_DIR/transactions
mkdir -p $LOG_DIR/end_code_output
if [ ! -f $LOG_DIR/cfg.yaml ]; then
    cp $BASE_DIR/cfg_temp.yaml $LOG_DIR/cfg.yaml
fi

# gdrive
# ======
FILE=$HOME/.gdrive
if [ -f "$FILE" ]; then
    sudo chown $(whoami) -R $HOME/.gdrive
fi

echo -e "warning: Update the following file "$LOG_DIR"/.eudat_client.txt' with
your EUDAT account's password. Best to make sure the file is not readable or
even listable for anyone but you. You achieve this with:
'chmod 700 eudat_password.txt'"
echo ""
yes_or_no "Are you are a provider" && provider_setup

# LOG_PATH
# ========
# line_new=$LOG_DIR
# var=$(echo $line_new | sed 's/\//\\\//g')
# sed -i.bak "s/^\(LOG_PATH=\).*/\1\"$var\"/" $LOG_DIR/.env
# rm -f $LOG_DIR/.env.bak


# line_new=$(which gdrive | sed 's/\//\\\//g')
# sed -i.bak "s/^\(GDRIVE=\).*/\1\"$line_new\"/" $LOG_DIR/.env
# rm -f $LOG_DIR/.env.bak

# EBLOCPATH
# =========
# eblocbrokerPath="$BASE_DIR"
# var=$(echo $eblocbrokerPath | sed 's/\//\\\//g')
# sed -i.bak "s/^\(EBLOCPATH=\).*/\1\"$var\"/" $LOG_DIR/.env
# rm $LOG_DIR/.env.bak

# User Name
# =========
# line_old="whoami"
# line_new=$(logname)

# sed -i.bak "s/^\(WHOAMI=\).*/\1\"$line_new\"/" $LOG_DIR/.env
# rm -f $LOG_DIR/.env.bak

# RPC PORT
# ========
# line_old="8545"
# sed -i.bak "s/^\(RPC_PORT=\).*/\1$line_old/" $LOG_DIR/.env
# rm $LOG_DIR/.env.bak

# configure_coinbase
# configure_oc
# configure_ipfs

## Setup
## sudo ln -s /usr/bin/node /usr/local/bin/node
# sudo chmod 700 /home/*

# PATH Name
# =========
# line_old="EBLOCBROKER_PATH"
# line_new=$(echo $BASE_DIR | sed 's/\//\\\//g')
# sed -i.bak 's/'$line_old'/'$line_new'/' $LOG_DIR/.env
# rm -f $LOG_DIR/.env.bak
# sed -i.bak "s/^\(EBLOCBROKER_PATH=\).*/\1\"$line_new\"/" $DIR/slurm_mail_prog.sh
# rm -f $DIR/slurm_mail_prog.sh.bak
