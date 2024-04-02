from requests_tor import RequestsTor
from datetime import datetime

url = 'http://svomhrvjpp3czbo3ryatvvj46nkseaq3p5nzpik76scyenfgw3xss4id.onion/api/event_bucket'  # Replace this with your onion address
rt = RequestsTor(tor_ports=(9050,), tor_cport=9051)

data={'sender':'shabd',
      'content':'hi'}

r = rt.post(url,json=data)
print(r.text)
