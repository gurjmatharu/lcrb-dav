import socketio  # Installed with 'pip install python-socketio`
import uvicorn
from fastapi import FastAPI

# Create a FastAPI instance
app = FastAPI()

# Create a test websocket server
# TODO: This needs to be shared with age_verification.py and acapy_handler.py
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.event
async def connect(sid, socket):
    print("connected", sid)
    await sio.emit("message", {"data": "I'm a real boy!"})


@sio.event
def disconnected(sid):
    print("disconnected", sid)


sio_app = socketio.ASGIApp(socketio_server=sio)

app.mount("/ws", sio_app)

uvicorn.run(app, host="localhost", port=5100)
