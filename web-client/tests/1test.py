import requests

# Onion address to make POST request to
onion_address = 'http://svomhrvjpp3czbo3ryatvvj46nkseaq3p5nzpik76scyenfgw3xss4id.onion'  # Replace this with your onion address

# Data to be sent in the POST request
from datetime import datetime
data={'type':'message','timestamp':datetime.now(),'sender':'shabd','content':{'message':'hi'}}

try:
    response = requests.post(onion_address, data=data)
    if response.status_code == 200:
        print("POST request successful.")
        print("Response:")
        print(response.text)
    else:
        print(f"POST request failed with status code: {response.status_code}")
except requests.exceptions.RequestException as e:
    print("Error making POST request:", e)
