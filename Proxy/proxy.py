# Import the needed libraries:
import argparse
import random
import mysql.connector
from pythonping import ping
from flask import Flask, jsonify, request


app = Flask(__name__)

# passing the ip addresses of the master and the workers:
master_dns = ""
workers_dns = []

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

# Direct hit for insert SQL querries to the master node:
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

# Direct hit for select SQL queries to the master node:
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

# Random method of the proxy that send a SQL select query withe the random implementation:
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

# Custom method of the proxy that sends the SQL query with the custom implementation:
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

# Main program of the proxy flask app:
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080)