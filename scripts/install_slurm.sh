#!/bin/bash

sudo apt-get update
grep -vE '^#' package_slurm.list | xargs -n1 sudo apt install -yf
sudo apt autoremove -y

# apt-cache search mysql | grep "dev"
# sudo apt-get install libmysqld-dev
# sudo apt-get install libmysqlclient

# slurm
# =====
sudo mkdir -p /var/log/slurm
sudo chown $(whoami) -R /var/log/slurm

git clone https://github.com/SchedMD/slurm $HOME/slurm
cd $HOME/slurm
git checkout e2e21cb571ce88a6dd52989ec6fe30da8c4ef15f  # slurm-19-05-8-1
sudo rm -rf /usr/local/lib/slurm/ /tmp/slurmstate/
make clean
./configure --enable-debug --enable-front-end
# ./configure --enable-debug --enable-front-end --enable-multiple-slurmd  # # seems like this also works
sudo make
sudo make install

# configurations
# ==============
sudo groupadd eblocbroker
sudo cp ~/ebloc-broker/broker/_slurm/confs/slurm.conf /usr/local/etc/slurm.conf
sudo cp ~/ebloc-broker/broker/_slurm/confs/slurmdbd.conf /usr/local/etc/slurmdbd.conf
sudo chmod 660 /usr/local/etc/slurm.conf  # 0600 , 755 ?
sudo chmod 660 /usr/local/etc/slurmdbd.conf
sudo chown munge:munge /etc/munge/munge.key
sudo chmod 400 /etc/munge/munge.key
sudo systemctl enable munge
sudo systemctl start munge
mkdir -p /tmp/run

#: https://askubuntu.com/a/556387/660555
sudo DEBIAN_FRONTEND=noninteractive apt-get install mailutils  # postfix
# sudo systemctl enable slurmctld  # Controller
# sudo systemctl enable slurmdbd  # Database
# sudo systemctl enable slurmd  # Compute Nodes
