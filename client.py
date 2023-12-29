import requests

def send_sql_query(url, endpoint, query):
    full_url = f"{url}/{endpoint}"
    headers = {"Content-Type": "application/sql"}
    response = requests.post(full_url, headers=headers, data=query)
    return response.text

def select_request(url, type, query):
    return send_sql_query(url+"/"+type, "select_endpoint", query)

def insert_request(url, type, query):
    return send_sql_query(url+"/"+type, "insert_endpoint", query)

def parameterized_select_request(url, type, query_template, params):
    full_query = query_template % params
    return send_sql_query(url+"/"+type, "select_endpoint", full_query)

def parameterized_insert_request(url, type, query_template, params):
    full_query = query_template % params
    return send_sql_query(url+"/"+type, "insert_endpoint", full_query)

if __name__ == '__main__':

    # Launching the request to the gatekeeper:
    gatekeeper_url = "http://170.12.25.6"
    select_query = "SELECT * FROM city;"
    insert_query = "INSERT INTO city (city_id, city) VALUES ('6', 'Ispahan');"
    parameterized_select_template = "SELECT * FROM city WHERE column = %s;"
    parameterized_select_params = ("some_value",)
    parameterized_insert_template = "INSERT INTO film (title, release_year) VALUES (%s, %s);"
    parameterized_insert_params = ("value1", "value2")

    print("Select Request:")
    print(select_request(gatekeeper_url, "random", select_query))

    print("\nInsert Request:")
    print(insert_request(gatekeeper_url, "direct", insert_query))

    print("\nParameterized Select Request:")
    print(parameterized_select_request(gatekeeper_url, "cutomize", parameterized_select_template, parameterized_select_params))

    print("\nParameterized Insert Request:")
    print(parameterized_insert_request(gatekeeper_url, "direct",parameterized_insert_template, parameterized_insert_params))
