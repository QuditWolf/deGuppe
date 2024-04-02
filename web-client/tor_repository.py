import os

from stem.control import Controller
import stem.process
from stem.util import term

import requests
from datetime import datetime

from tor_request import TorRequest

class tor_repo():
    def __init__(self,
                 key = "./my_service.key.key",
                 SOCKS_PORT = 9050,
                 password = None,
                 start_tor = True):

        self.key_path = os.path.expanduser(key)
        self.SOCKS_PORT = SOCKS_PORT
        if start_tor and not self._tor_process_exists():
            self.start_tor()
        self.tr = TorRequest()
        
    def _tor_process_exists(self):
        try:
            ctrl = Controller.from_port(port=self.SOCKS_PORT+1)
            ctrl.close()
            return True
        except:
            return False

    def start_tor(self):
        # Start an instance of Tor configured. This prints
        # Tor's bootstrap information as it starts. Note that this likely will not
        # work if you have another Tor instance running.

        def print_bootstrap_lines(line):
          if "Bootstrapped " in line:
            print(term.format(line, term.Color.BLUE))
        
        print(term.format("Starting Tor:\n", term.Attr.BOLD))
        self.tor_process = stem.process.launch_tor_with_config(
                config = {
                    'ControlPort': str(self.SOCKS_PORT+1),
                    'SocksPort': str(self.SOCKS_PORT),
                    'Log': [
                        'NOTICE stdout',
                        'ERR file ./tor_error_log',
                        ]
                    },
                init_msg_handler = print_bootstrap_lines,
                take_ownership = True,
                )

    def stop_tor(self):
        self.tor_process.kill()  # stops tor
    
    def start_tunnel(self, tunnels = {80:8000}):

        self.controller = Controller.from_port()
        self.controller.authenticate()

        if not os.path.exists(self.key_path):
            self.service = self.controller.create_ephemeral_hidden_service(tunnels, await_publication = True)
            print("Started a new hidden service with the address of %s.onion" % self.service.service_id)
            
            with open(self.key_path, 'w') as key_file:
              key_file.write('%s:%s' % (self.service.private_key_type, self.service.private_key))
        else:
            with open(self.key_path) as key_file:
              key_type, key_content = key_file.read().split(':', 1)

            self.service = self.controller.create_ephemeral_hidden_service({80: 8000},
                                                                 key_type = key_type,
                                                                 key_content = key_content,
                                                                 await_publication = True)
            print("Resumed %s.onion" % self.service.service_id)

    def close_tunnel(self):
        self.controller.remove_ephemeral_hidden_service(self.service.service_id)
        print("Closed %s.onion" % self.service.service_id)
        self.controller.close()

    def post(self,url,data):
        response = self.tr.post('http://'+ url+'/api/event_bucket', json=data)
        print(response, response.json)  # not your IP address
      #r = rt.post(url,json=data)


if __name__=="__main__":
    tt = tor_repo(start_tor=False)
    tt.post("http://"+input(),{})

