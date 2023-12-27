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

# Sakila config:
sudo mysql -Bse "SOURCE sakila-schema.sql"
sudo mysql -Bse "SOURCE sakila-data.sql"

# Install sysbench:
sudo apt-get -y install sysbench