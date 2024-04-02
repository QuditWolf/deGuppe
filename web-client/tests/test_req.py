import requests

proxies = {'http':  'socks5://127.0.0.1:9050',
           'https': 'socks5://127.0.0.1:9050'}

print("first IP:", requests.get('https://ident.me', proxies=proxies).text)

with Controller.from_port(port = 9051) as controller:
    controller.authenticate("welcome")
    controller.signal(Signal.NEWNYM)
    
print("second IP:", requests.get('https://ident.me', proxies=proxies).text)
