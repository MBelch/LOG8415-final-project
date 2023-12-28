#!/bin/bash

sudo apt-get update
sudo apt-get install sysbench

# Connect to the mysql cluster with it ip adress:
mysql -h 18.234.232.119 -u root --password=root

# Prepare sysbench:
sysbench --mysql-host=sysbench --mysql-host=18.234.232.119 --mysql-user=root --mysql-password=root --mysql-db=sakila --table-size=100000 --tables=8 --threads=4 --time=300 prepare

# Run the benchmark:
sysbench --mysql-host=18.234.232.119 --mysql-user=root --mysql-password=root --mysql-db=sakila --table-size=100000 --tables=8 --threads=64 --time=300 --rand-type=uniform --report-interval=10 --db-ps-mode=disable --db-driver=mysql oltp_read_write run

sysbench --mysql-host=18.234.232.119 --mysql-user=root --mysql-password=root --mysql-db=sakila --table-size=100000 --tables=8 --threads=4 cleanup
