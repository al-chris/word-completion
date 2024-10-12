import socketio

sio = socketio.Client()

@sio.event
def connect():
    print("Test Client: Connected to server.")
    sio.emit("join", {"username": "testuser", "room": "testroom"})

@sio.event
def disconnect():
    print("Test Client: Disconnected from server.")

@sio.event
def joined(data):
    print(f"Test Client: Joined with UID: {data['uid']}")

@sio.event
def error(data):
    print(f"Test Client: Error - {data['message']}")

sio.connect("http://localhost:8000", wait_timeout=5)
sio.wait()
