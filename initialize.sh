#!/bin/bash

setup=0
RPC_PORT="8545" # Please change it if you have different RPC_PORT number.

# pre-installation
# ----------------
if [ $setup -eq 1 ]; then
    # What are correct permissions for /tmp ? I unintentionally set it
    # all public recursively. https://unix.stackexchange.com/a/71625/198423
    # =====================================================================
    sudo chmod 1777 /tmp
    sudo find /tmp -mindepth 1 -name '.*-unix' -exec chmod 1777 {} + -prune -o -exec chmod go-rwx {} +

    mkdir -p /tmp/run
    sudo groupadd eblocbroker # members eblocbroker

    ## Install python3.7
    sudo apt-get update
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt install python3.7
    sudo apt-get install python3.7-dev

    sudo apt-get install python3
    sudo apt-get install python3-venv
    sudo apt-get install python-pip

    # sudo update-alternatives --config python3
    sudo apt-get update
    sudo apt-get install unixodbc-dev
    sudo apt-get install python-dev

    python3.7 -m venv $HOME/venv  # python3.7 -m venv --without-pip ~/venv
    source $HOME/venv/bin/activate

    # Recover pip: sudo python3 -m pip uninstall pip && sudo apt install python3-pip --reinstall
    pip install --upgrade pip --user
    pip install wheel
    pip install -r requirements.txt

    # This is must https://stackoverflow.com/questions/714063/importing-modules-from-parent-folder
    pip install -e .
    # pip install -U matplotlib
    # pip install -U google-colab
    # pip install sphinx_rtd_theme

    ## npm
    wget -qO- https://deb.nodesource.com/setup_7.x | sudo bash -
    sudo npm install -g n # npm install --save
    sudo n latest
    sudo npm install -g --unsafe-perm=true --allow-root ganache-cli  # npm install -g ganache-cli
    # npm install web3
    # npm install web3_ipc
    # npm install dotenv

    machine_os=$(bash $HOME/eBlocBroker/bash_scripts/machine.sh)
    if [ "$machine_os" == "Mac" ]; then
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
        sudo apt-get install pigz
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
    sudo rm -rf /usr/local/go /usr/bin/go
    sudo apt-get update
    wget -c https://dl.google.com/go/go1.14.2.linux-amd64.tar.gz -O - | sudo tar -xz -C /usr/local
    # echo "export PATH=$PATH:/usr/local/go/bin" >> $HOME/.profile
    # or
    sudo rm -rf /usr/local/go /usr/bin/go
    cd $HOME && git clone https://github.com/udhos/update-golang && cd update-golang
    sudo ./update-golang.sh
    # -------------------------------------------------------------

    ## Install google-drive: ========================================
    go get github.com/prasmussen/gdrive
    gopath=$(go env | grep 'GOPATH' | cut -d "=" -f 2 | tr -d '"')
    echo 'export PATH=$PATH:'$(echo $gopath)'/bin' >> $HOME/.profile
    source $HOME/.profile
    gdrive about

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
