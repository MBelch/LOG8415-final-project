#!/bin/bash

sudo apt-get -y update

# Install mysql-server:
sudo apt-get -y install mysql-server 

# Create dir to sakila and change dir to it:
mkdir /home/ubuntu/sakila && cd /home/ubuntu/sakila 

# Download Sakila database files:
sudo wget https://downloads.mysql.com/docs/sakila-db.tar.gz  

# Unzip the .tar Sakila database files:
sudo tar -xvzf sakila-db.tar.gz

# Change dir to the Sakila directory:
cd /home/ubuntu/sakila/sakila-db

# Update the credentials:
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root'"

# Sakila config:
sudo mysql -u root --password=root -e "SOURCE sakila-schema.sql"
sudo mysql -u root --password=root -e "SOURCE sakila-data.sql" 

# Use database:
sudo mysql -u root --password=root -e "USE sakila"

# Install sysbench:
sudo apt-get -y install sysbench

# The benchmar on the stand-alone mysql-server:
sudo sysbench oltp_read_write --table-size=100000 --mysql-db=sakila --mysql-user=root --mysql-password=root prepare
sudo sysbench oltp_read_write --table-size=100000 --threads=6 --max-time=60 --max-requests=0 --mysql-db=sakila --mysql-user=root --mysql-password=root  run > /home/ubuntu/results.txt
sudo sysbench oltp_read_write --mysql-db=sakila --mysql-user=root --mysql-password=root cleanup