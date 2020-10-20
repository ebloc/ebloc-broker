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
sudo apt-get install mysql-server
sudo apt-get install software-properties-common
sudo apt-get install mysql-client
sudo apt-get install default-libmysqlclient-dev
sudo apt-get install libmysqld-dev
sudo apt-get install libmysqlclient-dev

```

```
git clone https://github.com/SchedMD/slurm
cd slurm
./configure --enable-debug --enable-multiple-slurmd | ./configure --enable-debug --enable-front-end
sudo make
sudo make install

sudo cp slurm.conf /usr/local/etc/slurm.conf
sudo cp slurmdbd.conf /usr/local/etc/slurmdbd.conf
```

6. Hostname setup:

```
name="home"
sudo hostnamectl set-hostname $name
hostname
```

7. Set things up for slurmdbd (the SLURM accounting daemon) in MySQL. !(slurm == $(username))!

Should run `sudo slurmdbd` on the background in order to register the slurm-user.

```
sudo /etc/init.d/mysql start
mysql -u root -p
create database slurm_acct_db;
CREATE USER 'slurm'@'localhost' IDENTIFIED BY '12345'; | create user 'slurm'@'localhost';
                                                       | ALTER USER 'slurm'@'localhost' IDENTIFIED BY '12345';
grant usage on *.* to 'slurm'@'localhost';
grant all privileges on slurm_acct_db.* to 'slurm'@'localhost';
flush privileges;
```

8. Cont

```
mkdir /var/log/slurm
```

Should run `sudo slurmdbd` on the background in order to register the slurm-user.

```
user_name=$(whoami)

sacctmgr add cluster home
sacctmgr add account $user_name
sacctmgr create user $user_name defaultaccount=$user_name adminlevel=None

# Following line is required only to remove
sacctmgr remove user where user=user_name
```

### Check registered provider and users

```
sacctmgr list cluster
sacctmgr show assoc format=account
sacctmgr show assoc format=account,user,partition where user=<user_name>

sacctmgr show user -s
```

-----------

# mysql

```
sudo su
mysql -u root -p   [ENTER]

SELECT User FROM mysql.user;
CREATE USER 'slurm'@'localhost' IDENTIFIED BY '12345';
        'slurm'==$(whoami)
```
