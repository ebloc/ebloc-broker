SET GLOBAL innodb_buffer_pool_size=402653184;
create database slurm_acct_db;
SET GLOBAL validate_password.policy = LOW;
CREATE USER 'alper'@'localhost' IDENTIFIED BY '12345678';  -- 'alper'=> $(whoami)
grant usage on *.* to 'alper'@'localhost';
grant all privileges on slurm_acct_db.* to 'alper'@'localhost';
flush privileges;
exit
