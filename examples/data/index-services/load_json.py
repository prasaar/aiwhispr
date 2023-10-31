import json
import requests

url_post = "http://127.0.0.1:10001/index"

f_in = open("./nike_data.json")
data_in = json.load(f_in)
# The API endpoint to communicate with

for new_data in data_in:
# A POST request to the API
    post_response = requests.post(url_post, json=new_data)
    # Print the response
    print(post_response)
