# Slurm Emulator Mode Setup

## Guide1: https://slurm.schedmd.com/faq.html#multi_slurmd
## Guide2: http://wildflower.diablonet.net/~scaron/slurmsetup.html

```
echo "$(whoami)@$(hostname)"
apt-cache search mysql | grep "-dev"
```

```
sudo apt-get update

sudo apt-get install build-essential gcc libmunge-dev libmunge2 munge mysql-server
sudo apt-get install mysql-client libmysqlclient-dev libmysqld-dev
sudo apt-get install libmysqlclient

sudo apt-get install default-libmysqlclient-dev
'''

'''
git clone https://github.com/SchedMD/slurm
cd slurm
./configure --enable-debug --enable-front-end
sudo make
sudo make install
```

sudo cp slurm.conf    /usr/local/etc/slurm.conf
sudo cp slurmdbd.conf /usr/local/etc/slurmdbd.conf

7. Set things up for slurmdbd (the SLURM accounting daemon) in MySQL. !(slurm == $(username))!

Should run `sudo slurmdbd` on the background in order to register the slurm-user.

```
sudo /etc/init.d/mysql start
mysql -u root -p
create database slurm_acct_db;
create user 'slurm'@'localhost';                                         | CREATE USER 'slurm'@'localhost' IDENTIFIED BY ‘12345’;
set password for 'slurm'@'localhost' = password('MyStoragePassword');    |
grant usage on *.* to 'slurm'@'localhost';
grant all privileges on slurm_acct_db.* to 'slurm'@'localhost';
flush privileges;
```

8. 

Should run `sudo slurmdbd` on the background in order to register the slurm-user.

```
userName=$(whoami)
sacctmgr add cluster cluster
sacctmgr add account $userName
sacctmgr create user $userName defaultaccount=$userName adminlevel=[None]

# Following line is required only to remove
sacctmgr remove user where user=userName
```

### Check registered cluster and users

```
sacctmgr show assoc format=account
sacctmgr show assoc format=account,user,partition where user=<userName>
sacctmgr list cluster
```

-----------

# mysql
sudo su
mysql -u root -p   [ENTER]

SELECT User FROM mysql.user;
CREATE USER 'slurm'@'localhost' IDENTIFIED BY '12345';
        'slurm'==$(whoami)