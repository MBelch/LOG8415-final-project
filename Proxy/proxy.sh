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
parser.add_argument("master_dns", help="Master's dns")
parser.add_argument("--workers_dns", nargs="+", help="Workers' dns")
args = parser.parse_args()
master_dns = args.master_dns
workers_dns = args.workers_dns

# Connexion to mysql method:
def mysql_connexion(host):
    try :
        connexion = mysql.connector.connect(user='root', host=host, database='sakila')
        print("Connexion established : ", host)
        return connexion
    except mysql.connector.Error as e:
        print(e)

# Get the lowest time response based on ping:
def lwst_ping_responce():
    pr = {}
    pr[master_dns] = ping(master_dns).rtt_avg_ms
    for e in workers_dns:
        pr[e] = ping(e).rtt_avg_ms
    lwst_ping_responce = min(pr, key=pr.get)
    return lwst_ping_responce

# Direct hit for insert querries to the master node:
@app.route("/direct", methods=["POST"])
def direct_insert():
    request_data = request.get_json()
    query = request_data['query']
    c = mysql_connexion(master_dns)
    cursor = mysql_connexion.cursor()
    cursor.execute(query)
    mysql_connexion.commit()
    cursor.close()
    c.close()
    return jsonify(message="Query POST to master successfull"), 201

# Direct hit for select queries to the master node:
@app.route("/direct", methods=["GET"])
def direct_select():
    request_data = request.get_json()
    query = request_data['query']
    c = mysql_connexion(master_dns)
    cursor = mysql_connexion.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    c.close()
    return jsonify(server="master", dns=master_dns, result=result), 200

# Random method of the proxy: 
@app.route("/random", methods=["GET"])
def random_select():
    request_data = request.get_json()
    query = request_data['query']
    w_node = random.choice(workers_dns)
    c = mysql_connexion(w_node)
    cursor = mysql_connexion.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    c.close()
    return jsonify(server="worker", dns=w_node, result=result), 200

# Custom method of the proxy:
@app.route("/custom", methods=["GET"])
def custom_select():
    request_data = request.get_json()
    query = request_data['query']
    w_node = lwst_ping_responce()
    c = mysql_connexion(w_node)
    cursor = mysql_connexion.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    c.close()
    if w_node == master_dns:
        server = "master"
    else:
        server = "worker"
    return jsonify(server=server, dns=w_node, result=result), 200

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
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

# Lanching the docker compose containing the container:
sudo docker compose up -d