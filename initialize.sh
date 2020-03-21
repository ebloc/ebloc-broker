#!/bin/bash

setup=0
rpcPort="8545" # Please change it if you have different RPC_PORT number.

# Update repository with the latest update
# git fetch --all && git reset --hard origin/master

# Pre-installation:-----------------------------------------
if [ $setup -eq 1 ]; then
    ## Upgrade geth on Ubuntu: ----------------------------
    # sudo apt-get install software-properties-common
    # sudo add-apt-repository -y ppa:ethereum/ethereum
    # sudo add-apt-repository -y ppa:ethereum/ethereum-dev
    # sudo apt-get upgrade ethereum
    #------------------------------------------------------

    ## Install Python3.6 on Ubuntu: -------------
    # sudo add-apt-repository ppa:deadsnakes/ppa
    # sudo apt-get update
    # sudo apt-get install python3.6
    #--------------------------------------------

    ## Python3.6 setup, required for all providers!
    sudo apt-get install python3-dev
    sudo apt-get install python3-venv
    sudo apt-get install python3.6-dev

    sudo apt install python-pip
    pip install wheel
    python3 -m venv $HOME/venv # python3.6 -m venv --without-pip venv
    source $HOME/venv/bin/activate

    # Recover pip: sudo python3 -m pip uninstall pip && sudo apt install python3-pip --reinstall
    pip install --upgrade pip --user

    pip install -r requirements.txt

    pip install -U web3        # pip install --upgrade web3 # pip install --pre --upgrade web3
    pip install -U pyocclient  # owncloud_py
    pip install -U typing      # (https://github.com/ethereum/web3.py/issues/736#issuecomment-378679295)
    pip install -U colored
    pip install -U pymongo
    pip install -U python-dotenv
    pip install -U matplotlib
    pip install -U pydot
    pip install -U google-colab
    pip install -e .  # This is must https://stackoverflow.com/questions/714063/importing-modules-from-parent-folder
    # pip install sphinx_rtd_theme

    ## npm
    wget -qO- https://deb.nodesource.com/setup_7.x | sudo bash -
    sudo npm install -g n # npm install --save
    sudo n latest
    sudo npm install -g --unsafe-perm=true --allow-root ganache-cli
    npm install -g minilock-cli
    # npm install web3
    # npm install web3_ipc
    # npm install dotenv

    machineOS=$(bash $HOME/eBlocBroker/scripts/machine.sh)
    if [ "$machineOS" == "Mac" ]; then
        brew install realpath # Mac Packages
    else
        ## Linux Packages
	sudo apt-get install munge
	sudo apt-get install mailutils
	sudo apt-get install curl

        sudo apt-get install davfs2
        sudo apt-get install python-psutil
        sudo apt-get install -y nodejs
        sudo apt-get install bc
        sudo apt-get install realpath
	sudo apt-get install acl
    fi

    # mongodb guide => https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/
    #
    # sudo mkdir /var/lib/mongodb
    # sudo mkdir /var/log/mongodb
    # sudo mkdir -p /data/db
    #
    # sudo chown -R mongodb:mongodb /var/lib/mongodb
    # sudo chown mongodb:mongodb /tmp/mongodb-27017.sock
    #
    # sudo service mongod start
    # service mongod status | systemctl status mongodb
    # ----------------------------------------------------------

    ## install go--------------------------------------------------
    sudo apt-get update
    wget https://dl.google.com/go/go1.14.linux-amd64.tar.gz
    sudo tar -xvf go1.14.linux-amd64.tar.gz
    rm -f go1.14.linux-amd64.tar.gz
    rm -rf /usr/local/go
    sudo mv go /usr/local
    echo "export PATH=$PATH:/usr/local/go/bin" >> $HOME/.profile
    # -------------------------------------------------------------

    ## Install google-drive: ========================================
    go get github.com/prasmussen/gdrive
    gopath=$(go env | grep 'GOPATH' | cut -d "=" -f 2 | tr -d '"')
    echo 'export PATH=$PATH:'$(echo $gopath)'/bin' >> $HOME/.profile
    source $HOME/.profile
    gdrive about
    # ===============================================================
    ## gdfuse
    # https://github.com/astrada/google-drive-ocamlfuse/wiki/Headless-Usage-&-Authorization

    # shared_with_me=true to have read-only access to all your "Shared with me" files under ./.shared.
    sed -i.bak "s/^\(download_docs=\).*/\1false/" $HOME/.gdfuse/me/config
    # https://github.com/astrada/google-drive-ocamlfuse/issues/499#issuecomment-430269233
    # download_docs=false
    sed -i.bak "s/^\(shared_with_me=\).*/\1true/" $HOME/.gdfuse/me/config
fi
# IPFS check
# nc IP PORT
# Should return: /multistream/1.0.0
