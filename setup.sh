#!/bin/bash
: '
sudo add-apt-repository ppa:git-core/ppa -y
sudo apt-get update
sudo apt-get install -y git net-tools openssh-server
git clone https://github.com/ebloc/ebloc-broker
'
# general
# =======
sudo add-apt-repository ppa:boost-latest/ppa
sudo add-apt-repository ppa:git-core/ppa -y
sudo apt-get update
sudo apt-get install -y git
sudo apt-get install -y net-tools
sudo apt-get install -y openssh-server
sudo apt-get install -y libboost-all-dev
sudo apt -y install cmake

cd ~/ebloc-broker
git checkout test
git pull --rebase -v
grep -vE '^#' package.list | xargs -n1 sudo apt install -yf

# nodejs
# ======
curl -sL https://deb.nodesource.com/setup_14.x | sudo bash -
sudo apt -y install nodejs
node -v

# go
# ==
# Add following lines into `.bashrc` text or `.zshrc`
export GOROOT=/usr/local/go
export GOPATH=/usr/local/go/bin/go
export PATH=$PATH:$GOROOT/bin:$GOPATH/bin
output=$(which go)
if [ "$output" == "" ]; then
    sudo apt-get purge -y golang*  # Remove the existing golang
    cd ~/
    tar_name="go1.17.3.linux-amd64.tar.gz"  # get latest version from: https://golang.org/dl/
    wget https://golang.org/dl/$tar_name
    tar -xvf $tar_name
    rm -f $tar_name
    sudo rm -rf /usr/local/go
    sudo mv go /usr/local
    go version
fi

# go-ipfs
# =======
ipfs_current_version=""
which ipfs &>/dev/null
if [ $? -eq 0 ]; then
    killall ipfs &>/dev/null
    ipfs_current_version=$(ipfs version | awk '{ print $3 }')
    echo ipfs_current_version=v$ipfs_current_version
fi

cd /tmp
version=$(curl -L -s https://github.com/ipfs/go-ipfs/releases/latest | grep -oP 'Release v\K.*?(?= )' | head -n1)
echo "version_to_download=v"$version  # go-ipfs_${version}_linux-386.tar.gz

if [[ "$ipfs_current_version" == "$version" ]]; then
    echo "## Latest version is already downloaded"
else
    wget $(echo https://dist.ipfs.io/go-ipfs/v${version}/go-ipfs_v${version}_linux-amd64.tar.gz)
    tar -xvf go-ipfs_v${version}_linux-amd64.tar.gz
    cd go-ipfs
    sudo bash install.sh
    cd /tmp
    rm -f go-ipfs*.tar.gz*
    rm -rf go-ipfs/
    echo "==> $(ipfs version)"
fi

# go-geth
# =======
sudo add-apt-repository -y ppa:ethereum/ethereum
sudo apt-get -y install ethereum

# ganache-cli
# ===========
sudo npm install -g ganache-cli
# npm i --package-lock-only
# npm audit fix

# python
# ======
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt install -y python-dev python3.7 python3-pip python3-virtualenv python3-venv python2 python-psutil
/bin/python3 -m pip install --upgrade pip

## apt and pip packages for ebloc-broker
sudo -H pip install --upgrade pip
python -m pip install --upgrade pip
python3.7 -m pip install --upgrade pip

# mongodb
# =======
curl -fsSL https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | \
    sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list
sudo apt update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod.service
sudo systemctl status mongod

# ebloc-broker pip packages
# =========================
VENV=$HOME/venv
python3.8 -m venv $VENV
source $VENV/bin/activate
$VENV/bin/python3.8 -m pip install --upgrade pip
pip install wheel
pip install dbus-python
pip install pycairo
cd ~/ebloc-broker
pip install -e . --use-deprecated=legacy-resolver

sudo chown $(logname) -R /home/ubuntu/.cache

black_version=$(pip freeze | grep black | sed 's|black==||g')
if [ "$output" != "" ]; then
    mkdir -p /home/alper/.cache/black/$black_version/
fi

# solc
mkdir ~/.solcx
cd ~/.solcx
     # https://solc-bin.ethereum.org/linux-amd64/solc-linux-amd64-v0.8.10+commit.fc410830
wget https://solc-bin.ethereum.org/linux-amd64/solc-linux-amd64-v0.7.6+commit.7338295f
chmod +x solc-linux-amd64-v0.7.6+commit.7338295f
mv solc-linux-amd64-v0.7.6+commit.7338295f solc-v0.7.6
rm -f solc-v0.8.10

empyt_folder=~/ebloc-broker/empty_folder
mkdir $empyt_folder && cd $empyt_folder
brownie init
rm -rf $empyt_folder
$HOME/ebloc-broker/broker/python_scripts/add_bloxberg_into_network_config.py
cd ~

# Set Universal Time (UTC) in Ubuntu
# Required for sync with Bloxberg blockchain
sudo apt install systemd-timesyncd
sudo timedatectl set-timezone UTC
sudo timedatectl set-ntp true
sudo systemctl restart systemd-timesyncd.service
systemctl status systemd-timesyncd
timedatectl status

yes_or_no () {
    while true; do
        read -p "$* [y/n]: " yn
        case $yn in
            [Yy]*) return 0  ;;
            [Nn]*) echo "end" ; return  1 ;;
        esac
    done
}

provider_setup () {
    # mailutils
    # =========
    sudo apt-get install mailutils -y

    # slurm
    # =====
    git clone https://github.com/SchedMD/slurm $HOME/slurm
    cd $HOME/slurm
    git checkout e2e21cb571ce88a6dd52989ec6fe30da8c4ef15f  #slurm-19-05-8-1
    sudo rm -rf /usr/local/lib/slurm/ /tmp/slurmstate/
    make clean
    ./configure --enable-debug --enable-front-end
    sudo make
    sudo make install
    sudo cp ~/ebloc-broker/_slurm/confs/slurm.conf /usr/local/etc/slurm.conf
    sudo cp ~/ebloc-broker/_slurm/confs/slurmdbd.conf /usr/local/etc/slurmdbd.conf
    #
    sudo chmod 0600 /usr/local/etc/slurmdbd.conf
    sudo chmod 0600 /usr/local/etc/slurm.conf
    sudo chown $(whoami) /usr/local/etc/slurmdbd.conf
    sudo chown munge:munge /etc/munge/munge.key
    sudo chmod 400 /etc/munge/munge.key

    sudo systemctl enable slurmctld
    sudo systemctl enable slurmdbd
    sudo systemctl enable munge
    sudo systemctl start munge

    # mysql
    # =====
    sudo apt update
    sudo apt install -y mysql-server
    sudo apt-get install -y libmunge-dev libmunge2 munge
    sudo apt-get install -y mysql-client libmysqlclient-dev default-libmysqlclient-dev

    mkdir -p /tmp/run
    sudo groupadd eblocbroker
}

yes_or_no "Are you a provider? Yes for slurm installation" && provider_setup

# finally
# =======
sudo apt autoclean -y
sudo apt autoremove -y
