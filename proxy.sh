#!/bin/bash

# Install Docker Engine on Ubuntu:
sudo apt-get -y update
sudo apt-get -y install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Install Docker compose: 
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get -y update

# To install the latest version
sudo apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Create a directory for the flask compose project:
mkdir /home/ubuntu/proxy && cd /home/ubuntu/proxy 

# Create the proxy Flask app:
cat <<EOL > /home/ubuntu/proxy/proxy.py
import argparse
import random
import mysql.connector
from pythonping import ping
from flask import Flask, jsonify, request


app = Flask(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("master_private_dns", help="Master's priavte dns")
parser.add_argument("--slaves_dns", nargs="+", help="List of private slaves dns")
args = parser.parse_args()

master_private_dns = args.master_private_dns
slaves_dns = args.slaves_dns

# Connect to mysql database
def mysql_cnx(target_dns):
    try :
        cnx = mysql.connector.connect(user='root',
                                    host=target_dns,
                                    database='sakila')
        print("Connected to database at: " + target_dns)
        return cnx
    except mysql.connector.Error as err:
        print("Connection to database error: {}".format(err))

# Find best connection target based on ping
def best_cnx_target():
    ping_responses = {}
    ping_responses[master_private_dns] = ping(master_private_dns).rtt_avg_ms
    for target_dns in slaves_dns:
        ping_responses[target_dns] = ping(target_dns).rtt_avg_ms

    best_cnx_target = min(ping_responses, key=ping_responses.get)
    return best_cnx_target

# Insert query
def insert(mysql_cnx, query):
    cursor = mysql_cnx.cursor()
    cursor.execute(query)
    mysql_cnx.commit()
    cursor.close()

# Select query
def select(mysql_cnx, query):
    cursor = mysql_cnx.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result

# Redirect direct insert queries to the master instance
@app.route("/direct", methods=["POST"])
def direct_post():
    request_data = request.get_json()
    query = request_data['query']
    cnx = mysql_cnx(master_private_dns)
    insert(cnx, query)
    cnx.close()
    return jsonify(message="Query POST to master successfull"), 201

# Redirect direct select queries to the master instance
@app.route("/direct", methods=["GET"])
def direct_get():
    request_data = request.get_json()
    query = request_data['query']
    cnx = mysql_cnx(master_private_dns)
    result = select(cnx, query)
    cnx.close()
    return jsonify(server="master", dns=master_private_dns, result=result), 200

# Redirect random select queries to a random slave instance
@app.route("/random", methods=["GET"])
def random_get():
    request_data = request.get_json()
    query = request_data['query']
    target_dns = random.choice(slaves_dns)
    cnx = mysql_cnx(target_dns)
    result = select(cnx, query)
    cnx.close()
    return jsonify(server="slave", dns=target_dns, result=result), 200

# Redirect custom select queries to the best instance
@app.route("/custom", methods=["GET"])
def custom_get():
    request_data = request.get_json()
    query = request_data['query']
    target_dns = best_cnx_target()
    cnx = mysql_cnx(target_dns)
    result = select(cnx, query)
    cnx.close()
    if target_dns == master_private_dns:
        server = "master"
    else:
        server = "slave"
    return jsonify(server=server, dns=target_dns, result=result), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080)
EOL

# Create requirements file:
cat <<EOL > /home/ubuntu/proxy/requirements.txt
flask
argparse
mysql.connector
pythonping
random
EOL

# Create a dockerfile:
cat <<EOL > /home/ubuntu/proxy/Dockerfile
# syntax=docker/dockerfile:1
FROM python:3.9
WORKDIR /code
ENV FLASK_APP=flask_app.py
ENV FLASK_RUN_HOST=0.0.0.0
RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
EXPOSE 5000
COPY . .
CMD ["flask", "run"]
EOL

# Creating the YAML compose file having the services of the two containers :
cat <<EOL > /home/ubuntu/proxy/compose.yaml
services:
  webapp:
    build: .
    ports:
      - "5000:5000"
EOL

# Lanching the docker compose containing the 2 containers:
sudo docker compose up -d