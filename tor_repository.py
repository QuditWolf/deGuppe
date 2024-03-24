import os
from stem.control import Controller

class tor_tunnel():
    def __init__(self, key = "./my_service.key"):
        self.key_path = os.path.expanduser(key+".key")

    def start_tunnel(self, tunnels = {80:5000}):

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

            self.service = self.controller.create_ephemeral_hidden_service({80: 5000},
                                                                 key_type = key_type,
                                                                 key_content = key_content,
                                                                 await_publication = True)
            print("Resumed %s.onion" % self.service.service_id)

    def close_tunnel(self):
        self.controller.remove_ephemeral_hidden_service(self.service.service_id)
        print("Closed %s.onion" % self.service.service_id)
        self.controller.close()
