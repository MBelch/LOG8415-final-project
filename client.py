import requests

# function for sending the SQL query as HTTP request to the gatekeeper architecture:
def send_sql_query(url, endpoint, query):
    full_url = f"{url}/{endpoint}"
    headers = {"Content-Type": "application/sql"}
    response = requests.post(full_url, headers=headers, data=query)
    return response.text

def select_request(url, type, query):
    # fucntion for select query request taking in it's arguments the url of the
    # gatekeeper, the type of the implementatio of the proxy and the SQL query, it uses 
    # send_sql_query method defined above
    return send_sql_query(url+"/"+type, "select_endpoint", query)

def insert_request(url, type, query):
    # fucntion for insert query request taking in it's arguments the url of the
    # gatekeeper, the type of the implementatio of the proxy and the SQL query, it uses 
    # send_sql_query method defined above to send the request as HTTP request to the gatekeeper
    return send_sql_query(url+"/"+type, "insert_endpoint", query)

def parameterized_select_request(url, type, query_template, params):
    # fucntion for a parameterized select query request taking in it's arguments the url of the
    # gatekeeper, the type of the implementatio of the proxy and the SQL query, it uses 
    # send_sql_query method defined above to send the request as HTTP request to the gatekeeper
    # and see how the gatekeeper will manage it    
    full_query = query_template % params
    return send_sql_query(url+"/"+type, "select_endpoint", full_query)

def parameterized_insert_request(url, type, query_template, params):
    # fucntion for a parameterized insert query request taking in it's arguments the url of the
    # gatekeeper, the type of the implementatio of the proxy and the SQL query, it uses 
    # send_sql_query method defined above to send the request as HTTP request to the gatekeeper
    # and see how the gatekeeper will manage it
    full_query = query_template % params
    return send_sql_query(url+"/"+type, "insert_endpoint", full_query)

# Main program of the client that sends the requests to the gatekeeper pattern:
if __name__ == '__main__':

    # defining the gatekeeper url and the SQL queries that will be sent to it:
    gatekeeper_url = "http://170.12.25.6"
    select_query = "SELECT * FROM city;"
    insert_query = "INSERT INTO city (city_id, city) VALUES ('6', 'Ispahan');"
    parameterized_select_template = "SELECT * FROM city WHERE column = %s;"
    parameterized_select_params = ("some_value",)
    parameterized_insert_template = "INSERT INTO film (title, release_year) VALUES (%s, %s);"
    parameterized_insert_params = ("value1", "value2")

    # Sending the select request to the gatekeeper:
    print("Select Request:")
    print(select_request(gatekeeper_url, "random", select_query))

    # Sending insert request to gatekeeper:
    print("\nInsert Request:")
    print(insert_request(gatekeeper_url, "direct", insert_query))

    # Sending the parameterized query to the gatekeeper with a undefined malicious proxy implementation
    # in order to see how the gatekeeper will manage this risk
    print("\nParameterized Select Request:")
    print(parameterized_select_request(gatekeeper_url, "cutomize@*-8", parameterized_select_template, parameterized_select_params))

    # Sending the parameterized insert query to the gatekeeper with a undefined malicious proxy implementation
    # in order to see how the gatekeeper will manage this risk. The risk is high because it's an insert malicious query
    print("\nParameterized Insert Request:")
    print(parameterized_insert_request(gatekeeper_url, "direct",parameterized_insert_template, parameterized_insert_params))
