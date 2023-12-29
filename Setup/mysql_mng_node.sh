#!/bin/bash

# Create dir for mysql-cluster :
sudo mkdir -p /opt/mysqlcluster/home
cd /opt/mysqlcluster/home

# Download the zipped file of mysql-cluster:
sudo wget http://dev.mysql.com/get/Downloads/MySQL-Cluster-7.2/mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz

# Unzip the zipped file:
sudo tar -zxvf mysql-cluster-gpl-7.2.1-linux2.6-x86_64.tar.gz
sudo ln -s mysql-cluster-gpl-7.2.1-linux2.6-x86_64 mysqlc

# Setup of executable paths:
# the first global variable setup: 
echo 'export MYSQLC_HOME=/opt/mysqlcluster/home/mysqlc' | sudo sh -c "cat >> /etc/profile.d/mysqlc.sh"
# the second global variable setup:
sudo echo 'export PATH=$MYSQLC_HOME/bin:$PATH' | sudo sh -c "cat >> /etc/profile.d/mysqlc.sh" 
source /etc/profile.d/mysqlc.sh

# Update and install libncurses5:
sudo apt-get -y update && sudo apt-get -y install libncurses5

# Creation of the Deployment Directory and Setup Config Files:
sudo mkdir -p /opt/mysqlcluster/deploy
cd /opt/mysqlcluster/deploy
sudo mkdir /opt/mysqlcluster/deploy/conf
sudo mkdir /opt/mysqlcluster/deploy/mysqld_data
sudo mkdir /opt/mysqlcluster/deploy/ndb_data
cd /opt/mysqlcluster/deploy/conf

# Setup the config file:
cat <<EOL > /opt/mysqlcluster/deploy/my.cnf 
[mysqld]
ndbcluster
datadir=/opt/mysqlcluster/deploy/mysqld_data
basedir=/opt/mysqlcluster/home/mysqlc
port=3306
EOL

cat <<EOL > /opt/mysqlcluster/deploy/config.ini
[ndb_mgmd]
hostname=18.234.232.119
datadir=/opt/mysqlcluster/deploy/ndb_data
nodeid=1

[ndbd default]
noofreplicas=3
datadir=/opt/mysqlcluster/deploy/ndb_data

[ndbd]
hostname=18.234.232.120
nodeid=3

[ndbd]
hostname=18.234.232.121
nodeid=4

[ndbd]
hostname=18.234.232.122
nodeid=5

[mysqld]
nodeid=50
EOL

# Initialize the database:
cd /opt/mysqlcluster/home/mysqlc
scripts/mysql_install_db –no-defaults –datadir=/opt/mysqlcluster/deploy/mysqld_data

# Start management node:
cd /opt/mysqlcluster/home/mysqlc/bin/
ndb_mgmd -f /opt/mysqlcluster/deploy/conf/config.ini –initial –configdir=/opt/mysqlcluster/deploy/conf 

# Create dir to sakila and change dir to it:
mkdir /opt/mysqlcluster/sakila && cd /opt/mysqlcluster/sakila 

# Download Sakila database files:
sudo wget https://downloads.mysql.com/docs/sakila-db.tar.gz  

# Unzip the .tar Sakila database files:
sudo tar -xvzf sakila-db.tar.gz

# Change dir to the Sakila directory:
cd /opt/mysqlcluster/sakila/sakila-db

# Update the credentials:
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root'"

# Sakila config:
sudo mysql -u root --password=root -e "SOURCE sakila-schema.sql"
sudo mysql -u root --password=root -e "SOURCE sakila-data.sql" 

# Use database:
sudo mysql -u root --password=root -e "USE sakila"

# Install sysbench:
sudo apt-get -y install sysbench

