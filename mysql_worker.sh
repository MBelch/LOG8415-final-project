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

# create ndb data dir:
mkdir -p /opt/mysqlcluster/deploy/ndb_data

# Start data node:
ndbd -c 18.234.232.119:1186

# Create dir to sakila and change dir to it:
mkdir /opt/mysqlcluster/sakila && cd /opt/mysqlcluster/sakila 

# Download Sakila database files:
sudo wget https://downloads.mysql.com/docs/sakila-db.tar.gz  

# Unzip the .tar Sakila database files:
sudo tar -xvzf sakila-db.tar.gz

# Change dir to the Sakila directory:
cd /opt/mysqlcluster/sakila/sakila-db

# Sakila config:
sudo mysql -Bse "SOURCE sakila-schema.sql"
sudo mysql -Bse "SOURCE sakila-data.sql"

# Install sysbench:
sudo apt-get -y install sysbench