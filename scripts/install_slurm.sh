#!/bin/bash

sudo apt-get update
xargs -a <(awk '! /^ *(#|$)/' ~/ebloc-broker/scripts/package_slurm.list) -r -- sudo apt install -yf
sudo apt install libmariadbclient-dev -y
sudo apt install libmariadb-dev -y

#: https://askubuntu.com/a/556387/660555
sudo DEBIAN_FRONTEND=noninteractive apt-get install mailutils  # postfix
sudo apt autoremove -y

# munge
# =====
sudo chown munge:munge /etc/munge/munge.key
sudo chmod 400 /etc/munge/munge.key
sudo systemctl enable munge
sudo systemctl start munge

# slurm
# =====
sudo mkdir -p /var/log/slurm
sudo chown $(whoami) -R /var/log/slurm
git clone --depth 1 --branch slurm-19-05-8-1 https://github.com/SchedMD/slurm.git ~/slurm
cd ~/slurm
sudo rm -rf /usr/local/lib/slurm/ /tmp/slurmstate/
make clean
./configure --enable-debug --enable-front-end  # --enable-multiple-slurmd  # seems like this also works
sudo make && sudo make install
scontrol --version
if [ $? -ne 0 ]; then
   echo scontrol [ FAIL ]
   exit 1
fi

# configurations
# ==============
sudo groupadd eblocbroker
sudo cp ~/ebloc-broker/broker/_slurm/confs/slurm.conf /usr/local/etc/slurm.conf
sudo cp ~/ebloc-broker/broker/_slurm/confs/slurmdbd.conf /usr/local/etc/slurmdbd.conf
sudo chmod 664 /usr/local/etc/slurm.conf  # 0600 , 755 , 660 , 755
sudo chmod 755 /usr/local/etc/slurmdbd.conf
mkdir -p /tmp/run

# apt-cache search mysql | grep "dev"
