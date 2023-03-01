#!/bin/bash

set-hostname () {
    sudo hostnamectl set-hostname $1;
    echo $(hostname -I | cut -d\  -f1) $(hostname) | sudo tee -a /etc/hosts;
    hostnamectl;
    exec zsh
}

mysql_init () {
    mysqld --initialize
    sudo /etc/init.d/mysql start
    sudo systemctl --no-pager status mysql
    sudo cp ~/ebloc-broker/scripts/slurm_mysql.sql /root/
    sudo su -c "mysql -u root < ~/slurm_mysql.sql"
}

compile_slurm () {
    scontrol --version && return

    # Compile, build and install SLURM from Git source
    SLURM_TAG="slurm-22-05-2-1"
    sudo mkdir -p /var/log/slurm
    sudo chown $(whoami) -R /var/log/slurm
    git clone --depth 1 -b $SLURM_TAG --single-branch https://github.com/SchedMD/slurm.git ~/slurm
    cd ~/slurm
    sudo rm -rf /usr/local/lib/slurm/ /tmp/slurmstate/
    make clean >/dev/null 2>&1
    git reset --hard
    git clean -fdx
    ./configure --with-hdf5=no --enable-debug --enable-multiple-slurmd
    # ./configure --enable-debug --enable-front-end  # seems like this also works
    sudo make
    sudo make -j 4 install
    sudo install -D -m644 \
         etc/cgroup.conf.example /etc/slurm/cgroup.conf.example \
         etc/slurm.conf.example /etc/slurm/slurm.conf.example

    sudo install -D -m600 etc/slurmdbd.conf.example /etc/slurm/slurmdbd.conf.example
    sudo install -D -m644 contribs/slurm_completion_help/slurm_completion.sh /etc/profile.d/slurm_completion.sh

    scontrol --version
    if [ $? -ne 0 ]; then
       echo "scontrol  [  FAIL  ]"
       exit 1
    fi
}

after_slurmdbd () {
    # run following commands if slurmdbd is successfully open
    mysql_init
    sudo slurmdbd && sleep 1
    USER=$(whoami)
    sacctmgr add cluster eblocbroker --immediate
    sacctmgr add account $USER --immediate
    sacctmgr create user $USER defaultaccount=$USER adminlevel=None --immediate
}

sudo apt-get update
sudo apt --fix-broken install -y
xargs -a <(awk '! /^ *(#|$)/' ~/ebloc-broker/scripts/package_slurm.list) -r -- \
      sudo apt install -yf

#: https://askubuntu.com/a/556387/660555
sudo DEBIAN_FRONTEND=noninteractive apt-get install mailutils -y && systemctl reload postfix
sudo apt autoremove -y
sudo apt --fix-broken install -y

# munge
# =====
sudo chown -R munge:munge /var/lib/munge
sudo chown munge:munge /etc/munge/munge.key
sudo chmod 400 /etc/munge/munge.key
sudo systemctl enable munge
sudo systemctl start munge
systemctl status -l munge
ls -ld /var/lib/munge

# configurations
# ==============
sudo groupadd eblocbroker
# set-hostname ocean

FILE="/usr/local/etc/slurm.conf"
[ ! -f $FILE ] && sudo cp ~/ebloc-broker/broker/_slurm/confs/slurm.conf $FILE

FILE="/usr/local/etc/slurmdbd.conf"
[ ! -f $FILE ] && sudo cp ~/ebloc-broker/broker/_slurm/confs/slurmdbd.conf $FILE

sudo chmod 664 /usr/local/etc/slurm.conf  # 0600 , 755 , 660 , 755
sudo chmod 0600 /usr/local/etc/slurmdbd.conf
# sudo chown $(whoami):root /usr/local/etc/slurm.conf
sudo chown $(whoami):root /usr/local/etc/slurmdbd.conf
mkdir -p /tmp/run

compile_slurm
echo ""
# sudo sed -i 's/^root:.*$/root:*:16231:0:99999:7:::/' /etc/shadow
sudo mkdir -p /etc/sysconfig/slurm /var/spool/slurmd /var/spool/slurmctld /var/log/slurm /var/run/slurm
sudo chown -R $(whoami):$(whoami) /var/spool/slurmd /var/spool/slurmctld /var/log/slurm /var/run/slurm
sudo slurmdbd && after_slurmdbd
