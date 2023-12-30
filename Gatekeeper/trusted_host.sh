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
mkdir /home/ubuntu/trusted_host && cd /home/ubuntu/trusted_host 

# Create the trusted_host Flask app:
cat <<EOL > /home/ubuntu/trusted_host/trusted_host.py
import sys
import paramiko
from flask import Flask, request

app = Flask(__name__)

# Configuration for the trusted host:
path = os.path.dirname(os.getcwd())
trusted_host_address = 
trusted_host_key_path = path+'/final_project_keypair.pem'
trusted_host_username = 'ubuntu'

# Configuration for the proxy:
proxy_address = ''
proxy_key_path = path+'/final_project_keypair.pem'
proxy_username = 'ubuntu'

def forward_request_to_trusted_host(request_data):
"Bellow the function that forwards the request/query to the proxy\
 with secured SSH connection and sending the request using\
 this protocol, the private key is the keypair created in the setup"
    try:
        # Create a SSH connection to the proxy using its IP address:
        ssh_proxy = paramiko.SSHClient()
        ssh_proxy.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        key_private_proxy = paramiko.RSAKey.from_private_key_file(proxy_key_path)
        ssh_proxy.connect(hostname=proxy_address, username=proxy_username, pkey=key_private_proxy)

        # Send the request to the trusted_host:
        command = f'sudo echo "{request_data}" >> received_request.txt'
        stdin, stdout, stderr = ssh_proxy.exec_command(command)

        # Check for errors during command execution:
        if stderr.read():
            print(f"Error while forwarding request: {stderr.read()}")
        else:
            print('====> Request forwarded to trusted host')
    # Returning the catched exception and show it in the output        
    except Exception as e:
        print("Error connecting to the proxy:", e)


@app.route('/receive_request', methods=['POST'])
def receive_request():
    "The function for the flask app of the trusted host that gets the request\
    from the trusted host and forwarding it to the proxy. If there is an exception\
    it prints it in the output for further logging management"
    try:
        request_data = request.get_data(as_text=True)
        forward_request_to_trusted_host(request_data)
        return 'Request received and forwarded to trusted host', 200
    except Exception as e:
        print("Error processing request:", e)
        return 'Internal Server Error', 500

# Main program of the trusted host Flask app:
if __name__ == '__main__':
    # Read the proxy mode given in the SSH command:
    mode = sys.argv[1]
    app.run(host='0.0.0.0', port=5000)

EOL

# Create requirements file:
cat <<EOL > /home/ubuntu/trusted_host/requirements.txt
flask
argparse
paramiko
sys
EOL

# Create a dockerfile:
cat <<EOL > /home/ubuntu/trusted_host/Dockerfile
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

# Creating the YAML compose file having the service of the Trusted host container:
cat <<EOL > /home/ubuntu/trusted_host/compose.yaml
services:
  webapp:
    build: .
    ports:
      - "5000:5000"
EOL

# Lanching the docker compose containing container of the trusted host:
# Flask app
sudo docker compose up -d