# Slurm Emulator Mode Setup

# Guide-1:  https://slurm.schedmd.com/faq.html#multi_slurmd
# Guide-2:  http://wildflower.diablonet.net/~scaron/slurmsetup.html

echo "$(whoami)@$(hostname)"

```
apt-cache search mysql | grep "-dev"
```

```
sudo apt-get update
sudo apt-get install libmunge-dev libmunge2 munge
sudo apt-get install mysql-server
sudo apt-get install mysql-client
sudo apt-get install libmysqlclient-dev libmysqld-dev
sudo apt-get install default-libmysqlclient-dev
sudo apt-get install libmysqlclient

git clone https://github.com/SchedMD/slurm
cd slurm
./configure --enable-debug --enable-front-end
sudo make install
```

sudo cp slurm.conf    /usr/local/etc/slurm.conf
sudo cp slurmdbd.conf /usr/local/etc/slurmdbd.conf

7. Set things up for slurmdbd (the SLURM accounting daemon) in MySQL. (slurm == username)
mysql -u root -p
create database slurm_acct_db;
create user 'slurm'@'localhost';                                         | CREATE USER 'slurm'@'localhost' IDENTIFIED BY ‘12345’;
set password for 'slurm'@'localhost' = password('MyStoragePassword');    |
grant usage on *.* to 'slurm'@'localhost';
grant all privileges on slurm_acct_db.* to 'slurm'@'localhost';
flush privileges;

8. sacctmgr add cluster cluster

9. sacctmgr add account slurm
   sacctmgr create user slurm  defaultaccount=slurm adminlevel=[None]

   sacctmgr remove user where user=slurm
   
-----------

sacctmgr show assoc format=account
sacctmgr list cluster

# mysql
sudo su
mysql -u root -p   [ENTER]

SELECT User FROM mysql.user;
CREATE USER 'slurm'@'localhost' IDENTIFIED BY '12345';
