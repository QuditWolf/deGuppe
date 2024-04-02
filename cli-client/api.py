from fastapi import FastAPI, Request
app=FastAPI()

import db
fake_db = []


import orjson
import json
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import dataclasses
from datetime import datetime
@dataclasses.dataclass
class Event(BaseModel):
    sender: str
    type: str
    timestamp: datetime
    content: dict


@app.get("/")
async def root():
    return {"messaage":"Hello World"}

@app.post("/send_event")
async def send_event(request: Request, event: Event):
    client_host = request.client.host
    #convert event to json_compatible_item_data
    event = jsonable_encoder(event)
    print(f"received event from {event['sender']} @ {client_host}")
    fake_db.append(event)
    db.log_event(event)
    
    return {"blockchain": fake_db} 


new_msgs = ["shabd:abc","fmg:backla","vip:lololo"]
@app.get("/get_new_messages")
async def get_new_msgs(): 
    global new_msgs
    temp = ""
    for i in new_msgs:
        temp += i + "|"
    temp2 = []
    for i in new_msgs:
        temp2.append(i+"a")
    new_msgs = temp2
    return temp

@app.get("/add_slip")
async def addslip(pid: int, disease: str = ""):
    return db.add_slip(pid,disease)

def log(tim,frome,msg):
    with open("msgs.csv",'a') as f:
        f.write(tim + "," +  frome +  "," + msg)
