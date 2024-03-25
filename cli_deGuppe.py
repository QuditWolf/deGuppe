#deChat.py
import os
import socket
import json
import ast
import time
import sys
import random
import sqlite3
import socks
from stem.control import Controller
from threading import Thread

import stem.process
from stem.util import term

SOCKS_PORT = 9050

# Start an instance of Tor configured. This prints
# Tor's bootstrap information as it starts. Note that this likely will not
# work if you have another Tor instance running.

def print_bootstrap_lines(line):
  if "Bootstrapped " in line:
    print(term.format(line, term.Color.BLUE))


print(term.format("Starting Tor:\n", term.Attr.BOLD))


tor_process = stem.process.launch_tor_with_config(
  config = {
    'ControlPort': '9151',
    'SocksPort': str(SOCKS_PORT),
    'Log': [
            'NOTICE stdout',
            'ERR file ./tor_error_log',
          ]

  },
  init_msg_handler = print_bootstrap_lines,
)

#SOCKS_PORT=9050
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', SOCKS_PORT)
# Perform DNS resolution through the socket
def getaddrinfo(*args):
  return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (args[0], args[1]))]
#socket.getaddrinfo = getaddrinfo

#print(term.format("\nChecking our endpoint:\n", term.Attr.BOLD))
#print(term.format(("https://ifconfig.me"), term.Color.BLUE))


#tor_process.kill()  # stops tor


filename="msgs"+str(random.randint(1,100))+".db"
con = sqlite3.connect(filename)
cur = con.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS msgs (
        frome VARCHAR(20),
        time VARCHAR(20),
        msg  VARCHAR(100));''')


strtodict=ast.literal_eval

hostname=socket.gethostname()   
IPAddr=socket.gethostbyname(hostname)   
HOST="0.0.0.0" #IPAddr
PORT=input("Enter port to run on(leave empty for 6666): ")
PORT=int(PORT) if PORT else 6666
#recvsock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#recvsock=socks.socksocket()
#recvsock.bind((HOST, PORT))

print(' * Connecting to tor')

controller=Controller.from_port()
controller.authenticate()

  # Create a hidden service where visitors of port 80 get redirected to local

key_path=os.path.expanduser('./my_service_key')
if not os.path.exists(key_path):
    print("Creating new service address")
    service = controller.create_ephemeral_hidden_service({81: PORT}, await_publication = True)
    print("Started a new hidden service with the address of %s.onion" % service.service_id)

    with open(key_path, 'w') as key_file:
      key_file.write('%s:%s' % (service.private_key_type, service.private_key))
else:
    with open(key_path) as key_file:
      key_type, key_content = key_file.read().split(':', 1)
    print("Found exiting key, resuming old service address")
    service = controller.create_ephemeral_hidden_service({81: PORT}, key_type = key_type, key_content = key_content, await_publication = True)
    print("Resumed old address of %s.onion" % service.service_id)

#response = controller.create_ephemeral_hidden_service({81: PORT}, await_publication = True)
#print(" * Our service is available at %s.onion, press ctrl+c to quit" % response.service_id)
print("Running deChat server on:")
print("%s @ %s"%(hostname, service.service_id + ".onion")) 
print("Press ctrl+c to quit")

def get_thread():
    con1 = sqlite3.connect(filename)
    cur1 = con1.cursor()
    print("Going to Listen")
    l=socket.socket()
    try:
        l.bind((HOST,PORT))
    except:
        print("address already in use")
        input("panic, you are on your own")
    l.listen()
    conn, addr = l.accept()
    #print(conn)
    while True:

        time_string = time.strftime("%H:%M:%S", time.localtime())
        with conn:
            while True:
                try:
                    datat = conn.recv(1024).decode()
                except:
                    pass
                if not datat:
                    break
                for data in datat.split("###"):
                    #print(data)
                    #event=json.loads(data)
                    try:
                        event=ast.literal_eval(data)
                        fromalias=event["fromalias"]
                        eventtype=event["type"]
                        if eventtype=="message":
                            msg=event["payload"]
                            #sys.stdout.write("\033[F")
                            print("\r[%s] <%s>: %s\n:"%(time_string,fromalias,msg),end="")
                            cur1.execute('INSERT INTO msgs VALUES("%s","%s","%s")'%(fromalias,time_string,msg))
                            con1.commit()
                    except:
                        if data:
                            print("Received message",data,end="")



def send_thread():
    con2 = sqlite3.connect(filename)
    cur2 = con2.cursor()
    s=socks.socksocket()
    HOST2= input("Talk to \n(empty for loopback)\n: ")
    if not HOST2:
        print("loopback")
        HOST2=service.service_id+".onion"

    PORT2=81
    myalias=input("Enter my name: ")
    #sendsock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST2, 81))
    print(f"Connected to",HOST2,PORT2)
    print(":",end="")
    while True:
        event={}
        event["type"]="message"
        event["fromalias"]=myalias
        event["payload"]=input()
        if not event["payload"]:
            continue
        print(":",end="")
        #data=json.dumps(event)+"###"
        data=str(event)+"###"
        s.sendall(data.encode())
        time_string = time.strftime("%H:%M:%S", time.localtime())
        cur2.execute('INSERT INTO msgs VALUES("%s","%s","%s")'%(myalias,time_string,event["payload"]))
        con2.commit()
        
print("Finally running")
try:
    outputThread = Thread(target=get_thread)
    inputThread = Thread(target=send_thread)
    outputThread.daemon=True
    inputThread.daemon=True
    outputThread.start()
    inputThread.start()
    outputThread.join()
    inputThread.join()
except:
    inputThread._running=False
    outputThread._running=False
    #eval(input("eval"))
    tor_process.kill()  # stops tor
    print("Exiting")
    #controller.remove_ephemeral_hidden_service(service.service_id)
if not list(cur.execute('SELECT * FROM msgs')):
    os.remove(filename)
