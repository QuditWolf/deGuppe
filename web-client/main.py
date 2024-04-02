from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from tor_repository import tor_repo
tor = tor_repo()
tor.start_tunnel()
app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

url = input("enter tor address")
sender = input("enter your nick")

manager = ConnectionManager()

from datetime import datetime
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

class Event(BaseModel):
    sender: str
    content: str

# get from outside(tor) send to local website
@app.post("/api/event_bucket")
async def chat(event: Event):
    print(f"Received {event}")
    sender = event.sender
    if sender:
#        if event.type == "user_connected":
#            response = {
#            "sender": sender,
#            "message": "got connected"
#            }
#        elif event.type == "user_disconnected":
#            response = {
#            "sender": sender,
#            "message": "got disconnected"
#            }
#        elif event.type == "message":
        response = {
            "sender": sender,
            "message": event.content
            }
        #repair and accept response from html side
        #await websocket.send_json(response)
        print(response)
        await manager.broadcast(f"{sender} wrote: {event.content}")

#to get from local website and send to other user via tor
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    await manager.broadcast(f"Client #{client_id} joined the chat")
    #todo tor broadcast join event
    tor.post(url,{"sender":sender, "content": "joined"})
    try:
        while True:
            print("while mein phasa")
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
            #todo send message via tor to all connected clients
            tor.post(url,{"sender":sender, "content": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
        #todo tor broadcast leave event
        tor.post(url,{"sender":sender, "content": "left"})

from fastapi.templating import Jinja2Templates

# locate templates
templates = Jinja2Templates(directory="templates")

@app.get("/")
def get_home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.post("/api/start")
def get_register(senderr: str, urll: str):
    global url, sender
    url = urll
    sender = senderr
