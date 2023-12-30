from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Define a list of trusted hosts:
trusted_hosts = []

# Define the proxy's IP address and port:
private_proxy_ip = ""
proxy_port = 5000

def forward_to_proxy(request):
    #Bellow the method that forwards the requests to the trusted host and then to the
    #proxy this function permits the checking of the request either it's from 
    # a trusted host or from a malicious host from it's path pattern
    try:
        # Get the type of the request as it's direct, random or customized:
        rt = request_data.get('type')
        if rt not in ['direct','random','customized']:
            return jsonify({"status": "Access denied. Host not trusted."}), 403

        # Define the proxy URL
        proxy_url = f"http://{private_proxy_ip}:{proxy_port}/{rt}"

        # Forward the query to the proxy
        response = requests.post(proxy_url, json={"request": request})

        # Return the proxy response
        return response.json()

    except requests.RequestException as e:
        return {"error": "Proxy request failed:,"e}

@app.route('/check_request', methods=['POST'])
def check_request():
    # Function that does the first IP address checking of the trusted host
    # of the request received from the client and then forwared it the proxy before
    # a second checking form the trusted host whith SSH conection
    try:
        
        request = request.get_json()

        # Get the client's IP address:
        client_ip = request.remote_addr

        # Check if the client is a trusted host:
        if client_ip in trusted_hosts:

            # Forward the query to the proxy and wait for the response:
            response = forward_to_proxy(request)
            return jsonify({"status": "Query forwarded to the proxy.", "response": response})
        else:
            # Block the request
            return jsonify({"status": "Access denied. Host not trusted."}), 403
    # Print the exeception in the output:
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Main program of the gatekeeper flask app:
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
