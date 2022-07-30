#!/bin/bash


# Install MySQL Server in a Non-Interactive mode. Default root password will be "spmprx"
echo "mysql-server mysql-server-8.0.26/root_password password spmprx" | sudo debconf-set-selections
echo "mysql-server mysql-server-8.0.26/root_password_again password spmprx" | sudo debconf-set-selections
apt-get -y install mysql-server


# Run the MySQL Secure Installation wizard
mysql_secure_installation

#sed -i 's/127\.0\.0\.1/0\.0\.0\.0/g' /etc/mysql/mysql.conf.d/mysqld.cnf
sed -i '31 s/bind-address/#bind-address/' /etc/mysql/mysql.conf.d/mysqld.cnf
mysql -uroot -pspmprx -e 'USE mysql; UPDATE `user` SET `Host`="%" WHERE `User`="root" AND `Host`="localhost"; DELETE FROM `user` WHERE `Host` != "%" AND `User`="root"; FLUSH PRIVILEGES;'

mysql -u root -pspmprx  <feeddb.sql

cp mysqld.cnf /etc/mysql/mysql.conf.d/mysqld.cnf


