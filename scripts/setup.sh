#!/bin/bash
: '
git clone https://github.com/ebloc/ebloc-broker
cd ebloc-broker
git checkout dev && source scripts/setup.sh
'
GREEN="\033[1;32m";

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

mount_oc () {
    sudo mkdir -p /oc
    sudo chown $(whoami) /oc
    sudo chown -R $(whoami) /oc
    sudo apt-get install davfs2 -y
    sudo mount.davfs https://b2drop.eudat.eu/remote.php/webdav/ /oc
}

open_port_4001 () {  # ufw does not work on digital-ocean
    PORT=4001
    sudo systemctl enable ufw
    #
    sudo systemctl start firewalld
    sudo systemctl enable firewalld
    sudo firewall-cmd --add-port=$PORT/tcp --permanent
    sudo firewall-cmd --reload
    sudo firewall-cmd --list-all # --zone=docker
    sudo nmap localhost
}

ipfs_update () {
    CURRENT_DIR=$PWD
    ARCH=$(dpkg --print-architecture)
    command -v ipfs &>/dev/null
    if [ $? -eq 0 ]; then
        killall ipfs &>/dev/null
        ipfs_current_version=$(ipfs version | awk '{ print $3 }')
        echo ipfs_current_version=v$ipfs_current_version
    fi
    # IPFS_TAG=$(curl -L -s https://github.com/ipfs/go-ipfs/releases/latest | \
    #               grep -oP 'Release v\K.*?(?= )' | head -n1)
    IPFS_TAG=0.20.0  # override as wanted version
    echo "version_to_download=v"$IPFS_TAG
    if [[ "$ipfs_current_version" == "$IPFS_TAG" ]]; then
        echo "#> Wanted version is already installed"
    else
        cd /tmp
        wget "https://dist.ipfs.io/go-ipfs/v${IPFS_TAG}/go-ipfs_v${IPFS_TAG}_linux-${ARCH}.tar.gz"
        tar -xvf "go-ipfs_v${IPFS_TAG}_linux-${ARCH}.tar.gz"
        cd go-ipfs
        make install
        sudo ./install.sh
        cd /tmp
        rm -f "go-ipfs_v${IPFS_TAG}_linux-${ARCH}.tar.gz"
        rm -rf go-ipfs/
        ipfs version
    fi
    cd $CURRENT_DIR
}

install_ipfs () {
    ipfs version && return
    sudo systemctl start firewalld
    sudo systemctl enable firewalld
    sudo firewall-cmd --add-port=4001/tcp --permanent
    sudo firewall-cmd --reload
    sudo firewall-cmd --list-all
    sudo nmap localhost
    ipfs_update
    sudo sysctl -w net.core.rmem_max=2500000
    ipfs init --profile=lowpower,badgerds  # server,badgerds
    ipfs config Reprovider.Strategy roots
    ipfs config Routing.Type none
}

sudo add-apt-repository ppa:git-core/ppa -y
sudo apt-get update
sudo apt-get install -y git

cd ~/ebloc-broker
git checkout dev
git pull --rebase -v
~/ebloc-broker/scripts/package_update.sh

# nodejs
# ======
if [ "$(node -v)" == "" ];then
    curl -fsSL https://deb.nodesource.com/setup_17.x | sudo -E bash -
    sudo apt-get install -y nodejs
    node -v
fi

# npm
# ===
sudo aptitude install npm -y
sudo npm install -g npm
sudo npm install -g n
sudo npm config set fund false
sudo n latest
hash -r
npm config set update-notifier false
npm install -g npm@latest
npm install ganache --global
npm audit fix --force

# go
sudo snap install go --classic
go version

# ipfs
# =======
# ipfs init && sudo mount --bind ~/.ipfs ~/snap/ipfs/common
# echo "vm.max_map_count=262144" >> /etc/sysctl.conf
# sudo sysctl -p
install_ipfs
open_port_4001
sudo add-apt-repository -y ppa:ethereum/ethereum
sudo apt-get -y install ethereum

# python
# ======
sudo apt install libgirepository1.0-dev -y
sudo apt install libcairo2-dev -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt install software-properties-common -y
sudo apt-get update
sudo apt install python-dev -y
sudo apt install python2 -y
sudo apt install python-psutil -y
sudo apt install python3-dev -y
sudo apt install python3-pip -y
sudo apt install python3-venv -y
sudo apt install python3-virtualenv -y
sudo apt install python3.8 -y
sudo apt install python3.8-dev -y
sudo apt install python3.8-venv -y

# mongodb
# =======
install-mongo () {
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/6.0 multiverse" | \
        sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
    sudo apt-get update
    sudo apt-get install -y mongodb-org
    sudo mkdir -p /data/db
    sudo chown $(id -u) /data/db
    sudo mkdir -p /var/log/mongodb /var/lib/mongodb
    sudo chown -R mongodb. /var/log/mongodb
    sudo chown -R mongodb. /var/lib/mongodb
    sudo chown mongodb:mongodb /tmp/mongodb-27017.sock
    sudo systemctl unmask mongod
    sudo service mongod start
    sudo systemctl start mongod.service
    sudo systemctl unmask mongodb
    sudo systemctl enable mongod
    sudo systemctl --no-pager status --full mongod
    sudo chown mongodb:mongodb /tmp/mongodb-27017.sock
    mongo --eval 'db.runCommand({ connectionStatus: 1 })'
}

fix-black-package () {
    mkdir -p $HOME/.cache/black
    # sudo chown $(logname) -R $HOME/.cache/black
    black_version=$(pip freeze | grep black | sed 's|black==||g')
    if [ "$black_version" != "" ]; then
        rm -rf $HOME/.cache/black/*
        mkdir -p $HOME/.cache/black/$black_version
    fi
}

install_ebb_pip_packages () {
    VENV=$HOME/venv
    [ ! -d $VENV ] && command python3.8 -m venv $VENV
    source ${VENV}/bin/activate

    uname_out="$(uname -s)"
    case "${uname_out}" in
        Darwin*) # UNIX
            $VENV/bin/python3 -m pip install --disable-pip-version-check pip==21.3.1
            ;;
        *) # LINUX
            $VENV/bin/python3 -m pip install --upgrade pip
            ;;
    esac
    $VENV/bin/python3 -m pip install --upgrade wheel
    $VENV/bin/python3 -m pip install dbus-python==1.2.16
    cd ~/ebloc-broker && \
        $VENV/bin/python3 -m pip install -e . --use-deprecated=legacy-resolver && \
        fix-black-package
}

install-mongo
install_ebb_pip_packages

# solc
# ====
mkdir -p ~/.solcx
if [ "$(uname -i)" == "aarch64" ]; then
    sudo apt install -y libz3-dev
    sudo add-apt-repository ppa:ubuntu-toolchain-r/test
    sudo apt update
    sudo apt install -y g++-9
    ~/ebloc-broker/scripts/install_solc_0.7.6_deps.sh
    cd ~/.solcx
    wget https://github.com/ebloc/ebloc-helpful-binaries/raw/master/binaries/solc-v0.7.6-aarch64
    chmod +x solc-v0.7.6-aarch64
    solc-v0.7.6-aarch64 --version
    mv solc-v0.7.6-aarch64 solc-v0.7.6
else
    cd ~/.solcx
    rm -f solc-v0.8.*
    wget https://solc-bin.ethereum.org/linux-amd64/solc-linux-amd64-v0.7.6+commit.7338295f
    mv solc-linux-amd64-v0.7.6+commit.7338295f solc-v0.7.6
    chmod +x solc-v0.7.6
fi

~/ebloc-broker/broker/bash_scripts/folder_setup.sh

# Set Universal Time (UTC) in Ubuntu, required for sync with Bloxberg blockchain
sudo apt install -y systemd-timesyncd
sudo timedatectl set-ntp true
sudo timedatectl set-timezone UTC
sudo systemctl restart systemd-timesyncd.service
systemctl status --no-pager --full systemd-timesyncd
timedatectl status
sudo systemctl enable systemd-timesyncd

install_brownie () {
    empyt_folder=~/ebloc-broker/empty_folder
    mkdir -p $empyt_folder
    cd $empyt_folder
    brownie init
    cd ~ && rm -rf $empyt_folder
    ~/ebloc-broker/broker/python_scripts/add_bloxberg_into_network_config.py
    cd ~/ebloc-broker/contract/
    brownie compile
    cd ~
}
install_brownie

mkdir -p ~/git ~/docker
DIR=~/git/gdrive
[[ ! -d $DIR ]] && git clone https://github.com/prasmussen/gdrive.git ~/git/gdrive

go env -w GO111MODULE=auto
go get github.com/prasmussen/gdrive

echo ""
yes_or_no "Are you a provider? Yes for slurm installation" && ~/ebloc-broker/scripts/install_slurm.sh

# finally
# =======
sudo apt autoclean -y
sudo apt autoremove -y
sudo apt-get install -f -y
sudo apt --fix-broken install -y

eblocbroker about

gpg --gen-key
gpg --list-keys

# mount_oc
