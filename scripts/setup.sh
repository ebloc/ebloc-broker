#!/bin/bash
: '
git clone https://github.com/ebloc/ebloc-broker
cd ebloc-broker
git checkout dev && source scripts/setup.sh
'
RED="\033[1;31m"; GREEN="\033[1;32m"; BLUE="\033[1;36m"; NC="\033[0m"

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

# general
# =======
sudo add-apt-repository ppa:git-core/ppa -y
sudo apt-get update
sudo apt-get install -y git

cd ~/ebloc-broker
git checkout dev
git pull --rebase -v
~/ebloc-broker/scripts/package_update.sh

# nodejs
# ======
output=$(node -v)
if [ "$output" == "" ];then
   # curl -sL https://deb.nodesource.com/setup_14.x | sudo bash -
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

# ganache-cli
# ===========
# export NODE_OPTIONS=--openssl-legacy-provider
# sudo npm install -g ganache
hash -r
npm config set update-notifier false
npm install -g npm@latest
npm install ganache --global

# go
sudo snap install go --classic
go version

# ipfs
# =======
# alternative use snap to install ipfs:
# sudo snap install ipfs
# ipfs init && sudo mount --bind ~/.ipfs ~/snap/ipfs/common
open_port_4001 () {  # ufw does not work on digital-ocean
    sudo systemctl start firewalld
    sudo systemctl enable firewalld
    sudo firewall-cmd --add-port=4001/tcp --permanent
    sudo firewall-cmd --reload
    sudo firewall-cmd --list-all
    sudo nmap localhost
}

install_ipfs () {
    ipfs_current_version=""
    which ipfs &>/dev/null
    if [ $? -eq 0 ]; then
        killall ipfs &>/dev/null
        ipfs_current_version=$(ipfs version | awk '{ print $3 }')
        echo ipfs_current_version=v$ipfs_current_version
    fi
    cd /tmp
    version="0.11.0"
    echo "version_to_download=v"$version
    if [[ "$ipfs_current_version" == "$version" ]]; then
        echo "$GREEN##$NC Latest version is already downloaded"
    else
        kill -9 $(ps auxww | grep -E "[i]pfs"  | awk '{print $2}') > /dev/null 2>&1;
        arch=$(dpkg --print-architecture)
        wget "https://dist.ipfs.io/go-ipfs/v"$version"/go-ipfs_v"$version"_linux-"$arch".tar.gz"
        tar -xvf "go-ipfs_v"$version"_linux-"$arch".tar.gz"
        cd go-ipfs
        make install
        sudo ./install.sh
        cd /tmp
        rm -f "go-ipfs_v"$version"_linux-"$arch".tar.gz"
        rm -rf go-ipfs/
        ipfs version
        cd
    fi
    # https://github.com/ipfs/go-ipfs/issues/5534#issuecomment-425216890
    # https://github.com/ipfs/go-ipfs/issues/5013#issuecomment-389910309
    # set net.core.rmem_max: https://github.com/lucas-clemente/quic-go/wiki/UDP-Receive-Buffer-Size
    sudo sysctl -w net.core.rmem_max=2500000
    ipfs init --profile=server,badgerds
    ipfs config Reprovider.Strategy roots
    ipfs config Routing.Type none
    open_port_4001
}
# echo "vm.max_map_count=262144" >> /etc/sysctl.conf
# sudo sysctl -p
install_ipfs
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
sudo apt install python3.7 -y

# mongodb
# =======
curl -fsSL https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | \
    sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo chown -R mongodb. /var/log/mongodb
sudo chown -R mongodb. /var/lib/mongodb
sudo chown mongodb:mongodb /tmp/mongodb-27017.sock
sudo systemctl start mongod.service
sudo systemctl unmask mongodb
sudo systemctl enable mongod
sudo systemctl --no-pager status --full mongod

install_ebb_pip_packages () {
    VENV=$HOME/venv
    [ ! -d $VENV ] && python3 -m venv $VENV
    source $VENV/bin/activate
    $VENV/bin/python3 -m pip install --upgrade pip
    python3 -m pip install --no-use-pep517 cm-rgb
    $VENV/bin/python3 -m pip install wheel
    cd ~/ebloc-broker
    $VENV/bin/python3 -m pip install -e . --use-deprecated=legacy-resolver
    mkdir -p $HOME/.cache/black
    sudo chown $(logname) -R $HOME/.cache/black
    black_version=$(pip freeze | grep black | sed 's|black==||g')
    if [ "$black_version" != "" ]; then
        rm -rf $HOME/.cache/black/*
        mkdir -p $HOME/.cache/black/$black_version
    fi
}
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
sudo DEBIAN_FRONTEND=noninteractive apt-get install mailutils
systemctl reload postfix

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

gpg --gen-key
gpg --list-keys

mkdir -p ~/docker ~/git
git clone https://github.com/prasmussen/gdrive.git ~/git/gdrive
go env -w GO111MODULE=auto
go get github.com/prasmussen/gdrive

mount_oc () {
    sudo mkdir /oc
    sudo chown $(whoami) /oc
    sudo chown -R $(whoami) /oc
    sudo apt-get install davfs2 -y
    sudo mount.davfs https://b2drop.eudat.eu/remote.php/webdav/ /oc
}
# mount_oc

echo ""
yes_or_no "Are you a provider? Yes for slurm installation" && ~/ebloc-broker/scripts/install_slurm.sh

# finally
# =======
sudo apt autoclean -y
sudo apt autoremove -y
sudo apt-get install -f -y
sudo apt --fix-broken install -y
