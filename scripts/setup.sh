#!/bin/bash
: '
git clone https://github.com/ebloc/ebloc-broker
cd ebloc-broker
git checkout dev && source scripts/setup.sh
'
RED="\033[1;31m"
GREEN="\033[1;32m"
BLUE="\033[1;36m"
NC="\033[0m" # no Color

# general
# =======
sudo add-apt-repository ppa:git-core/ppa -y
sudo apt-get update
sudo apt-get install -y git
sudo apt-get install -y net-tools
sudo apt-get install -y openssh-server

cd ~/ebloc-broker
git checkout test
git pull --rebase -v
sudo apt-get update
grep -vE '^#' package.list | xargs -n1 sudo apt install -yf

# nodejs
# ======
curl -sL https://deb.nodesource.com/setup_14.x | sudo bash -
sudo apt -y install nodejs
sudo npm install -g npm
sudo npm install -g n
sudo n latest
node -v

# ganache-cli
# ===========
sudo npm install -g ganache-cli --unsafe-perm

# go
sudo snap install go --classic

# ipfs
# =======
# alternative: sudo snap install ipfs
#              ipfs init && sudo mount --bind ~/.ipfs ~/snap/ipfs/common
install_ipfs () {
    ipfs_current_version=""
    which ipfs &>/dev/null
    if [ $? -eq 0 ]; then
        killall ipfs &>/dev/null
        ipfs_current_version=$(ipfs version | awk '{ print $3 }')
        echo ipfs_current_version=v$ipfs_current_version
    fi
    cd /tmp
    version=$(curl -L -s https://github.com/ipfs/go-ipfs/releases/latest | grep -oP 'Release v\K.*?(?= )' | head -n1)
    echo "version_to_download=v"$version
    if [[ "$ipfs_current_version" == "$version" ]]; then
        echo "$GREEN##$NC Latest version is already downloaded"
    else
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
}
install_ipfs

# https://github.com/ipfs/go-ipfs/issues/5534#issuecomment-425216890
# https://github.com/ipfs/go-ipfs/issues/5013#issuecomment-389910309
ipfs init --profile=server,badgerds
ipfs config Reprovider.Strategy roots

# go-geth
# =======
sudo add-apt-repository -y ppa:ethereum/ethereum
sudo apt-get -y install ethereum

# python
# ======
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get update
sudo apt install -y python-dev
sudo apt install -y python2
sudo apt install -y python-psutil
sudo apt install -y python3-dev
sudo apt install -y python3-pip
sudo apt install -y python3-venv
sudo apt install -y python3-virtualenv
sudo apt install -y python3.7
sudo apt install -y python3.8-dev
sudo apt install -y python3.8-venv

# mongodb
# =======
curl -fsSL https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | \
    sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list
sudo apt update
sudo apt-get install -y mongodb-org
# sudo mkdir /var/lib/mongodb
# sudo mkdir /var/log/mongodb
sudo chown -R mongodb. /var/log/mongodb
sudo chown -R mongodb. /var/lib/mongodb
sudo chown mongodb:mongodb /tmp/mongodb-27017.sock
sudo systemctl start mongod.service
sudo systemctl --no-pager status --full mongod
sudo systemctl unmask mongodb
sudo systemctl enable mongod

# ebloc-broker pip packages
# =========================
VENV=$HOME/venv
python3.8 -m venv $VENV
source $VENV/bin/activate
$VENV/bin/python3.8 -m pip install --upgrade pip
sudo apt-get install -y libssl-dev zlib1g-dev gcc g++ make
pip install wheel
# pip install pycairo
# pip install dbus-python
cd ~/ebloc-broker
pip install -e . --use-deprecated=legacy-resolver

sudo chown $(logname) -R $HOME/.cache/black
black_version=$(pip freeze | grep black | sed 's|black==||g')
if [ "$black_version" != "" ]; then
    rm -rf $HOME/.cache/black/*
    mkdir -p $HOME/.cache/black/$black_version
fi

# solc
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
    chmod +x solc-linux-amd64-v0.7.6+commit.7338295f
    mv solc-linux-amd64-v0.7.6+commit.7338295f solc-v0.7.6
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

empyt_folder=~/ebloc-broker/empty_folder
mkdir $empyt_folder
cd $empyt_folder
brownie init
rm -rf $empyt_folder
cd $HOME
~/ebloc-broker/broker/python_scripts/add_bloxberg_into_network_config.py
cd ~/ebloc-broker/contract/
brownie compile

cd
gpg --gen-key
gpg --list-keys

sudo apt-get install davfs2 -y
sudo mkdir /oc
sudo chown $(whoami) /oc
sudo chown -R $(whoami) /oc
# sudo mount.davfs https://b2drop.eudat.eu/remote.php/webdav/ /oc
#------------------------------------------------------------------------------
# Provider
#------------------------------------------------------------------------------
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

provider_setup () {
    # slurm
    # =====
    git clone https://github.com/SchedMD/slurm $HOME/slurm
    cd $HOME/slurm
    git checkout e2e21cb571ce88a6dd52989ec6fe30da8c4ef15f  # slurm-19-05-8-1
    sudo rm -rf /usr/local/lib/slurm/ /tmp/slurmstate/
    make clean
    ./configure --enable-debug --enable-front-end
    sudo make
    sudo make install
    sudo cp ~/ebloc-broker/_slurm/confs/slurm.conf /usr/local/etc/slurm.conf
    sudo cp ~/ebloc-broker/_slurm/confs/slurmdbd.conf /usr/local/etc/slurmdbd.conf
    sudo chmod 0600 /usr/local/etc/slurmdbd.conf
    sudo chmod 0600 /usr/local/etc/slurm.conf
    sudo chown $(whoami) /usr/local/etc/slurmdbd.conf
    sudo chown munge:munge /etc/munge/munge.key
    sudo chmod 400 /etc/munge/munge.key
    sudo systemctl enable slurmctld
    sudo systemctl enable slurmdbd
    sudo systemctl enable munge
    sudo systemctl start munge

    mkdir -p /tmp/run
    sudo groupadd eblocbroker

    # mailutils
    # =========
    sudo apt-get install mailutils -y

    # mysql
    # =====
    sudo apt update
    sudo apt install -y mysql-server
    sudo apt-get install -y libmunge-dev libmunge2 munge
    sudo apt-get install -y mysql-client libmysqlclient-dev default-libmysqlclient-dev
}

echo ""
yes_or_no "Are you a provider? Yes for slurm installation" && provider_setup

# finally
# =======
sudo apt --fix-broken install
sudo apt autoclean -y
sudo apt autoremove -y
