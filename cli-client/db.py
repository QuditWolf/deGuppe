import orjson, json
import os

event_db_file = os.path.expanduser('./msgs.txt')
if not os.path.exists(event_db_file):
    with open(event_db_file, 'w'):
        pass

def log_event(event):
    with open(event_db_file, 'r') as fp:
        content = fp.read()
        if content:
            listObj = orjson.loads(content)
        else:
            listObj = []
        listObj.append(event)
    
    with open(event_db_file, 'w') as json_file:
        json.dump(listObj, json_file, 
                        indent=4,  
                        separators=(',',': '))
