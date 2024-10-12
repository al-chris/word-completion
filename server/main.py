# server/main.py
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create a Socket.IO server with explicit CORS settings
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=["*"])
app = FastAPI()
sio_app = socketio.ASGIApp(sio, other_asgi_app=app)

# Add CORS middleware to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# app.mount("/", sio_app)

# Connection Manager
class ConnectionManager:
    def __init__(self):
        self.rooms = {}  # room_name -> list of sid
        self.users = {}  # sid -> {"username": str, "room": str, "color": str}
        self.stories = {}  # room_name -> story string
        self.current_turn = {}   # room_name -> current sid

    async def join_room(self, sid, room, username, color):
        if room not in self.rooms:
            self.rooms[room] = []
            self.stories[room] = ""  # Initialize empty story
            self.current_turn[room] = sid  # First user gets the turn
        self.rooms[room].append(sid)
        self.users[sid] = {"username": username, "room": room, "color": color}
        await sio.enter_room(sid, room)
        # Notify others in the room
        await sio.emit("user_joined", {"uid": sid, "username": username}, room=room)
        # Broadcast whose turn it is
        await self.broadcast_turn(room)
        print(f"User '{username}' with SID '{sid}' joined room '{room}'.")

    async def broadcast_turn(self, room):
        current_sid = self.current_turn.get(room)
        if current_sid and current_sid in self.users:
            username = self.users[current_sid]['username']
            await sio.emit("turn_update", {"current_turn": username}, room=room)
            print(f"Turn updated in room '{room}' to '{username}'.")


    async def leave_room(self, sid):
        if sid in self.users:
            room = self.users[sid]['room']
            username = self.users[sid]['username']
            if room in self.rooms and sid in self.rooms[room]:
                self.rooms[room].remove(sid)
            await sio.leave_room(sid, room)
            del self.users[sid]
            # Notify others in the room
            await sio.emit("user_left", {"uid": sid, "username": username}, room=room)
            # If the user was the current turn, switch turn
            if self.current_turn.get(room) == sid:
                self.switch_turn(room)
                await self.broadcast_turn(room)
            print(f"User '{username}' with SID '{sid}' left room '{room}'.")


    async def append_to_story(self, sid, text):
        user = self.users.get(sid)
        if not user:
            await sio.emit("error", {"message": "You are not in a room"}, room=sid)
            return
        room = user['room']
        current_sid = self.current_turn.get(room)
        if sid != current_sid:
            await sio.emit("error", {"message": "It's not your turn"}, room=sid)
            return
        username = user['username']
        color = user['color']
        # Format the text with color tags
        formatted_text = f"[color={color}]{text} [/color]"
        # Append to the story
        self.stories[room] += formatted_text
        # Broadcast the updated story to all in the room
        await sio.emit("update_story", {"story": self.stories[room]}, room=room)
        print(f"Updated story in room '{room}': {formatted_text}")
        # Switch turn to next user
        self.switch_turn(room)
        # Broadcast the new turn
        await self.broadcast_turn(room)

    def switch_turn(self, room):
        sids = self.rooms.get(room, [])
        if not sids:
            self.current_turn.pop(room, None)
            return
        current_sid = self.current_turn.get(room)
        try:
            index = sids.index(current_sid)
            next_index = (index + 1) % len(sids)
            self.current_turn[room] = sids[next_index]
        except ValueError:
            # Current sid not in list, set to first
            self.current_turn[room] = sids[0]


    def get_all_rooms(self):
        return list(self.rooms.keys())

manager = ConnectionManager()

# Socket.IO Event Handlers
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    await manager.leave_room(sid)
    print(f"Client disconnected: {sid}")

@sio.event
async def join(sid, data):
    username = data.get('username')
    room = data.get('room')
    color = data.get('color')  # Expecting a hex color code, e.g., #FF0000
    if username and room and color:
        await manager.join_room(sid, room, username, color)
        # Send the current story to the newly joined user
        current_story = manager.stories.get(room, "")
        await sio.emit("update_story", {"story": current_story}, room=sid)
    else:
        await sio.emit("error", {"message": "Username, room, and color are required"}, room=sid)

@sio.event
async def create_room(sid, data):
    room = data.get('room')
    if room:
        if room not in manager.rooms:
            manager.rooms[room] = []
            manager.stories[room] = ""  # Initialize empty story
            await sio.emit("room_created", {"room": room}, room=sid)
            print(f"Room created: '{room}'.")
        else:
            await sio.emit("error", {"message": "Room already exists"}, room=sid)
    else:
        await sio.emit("error", {"message": "Room name is required"}, room=sid)

@sio.event
async def send_text(sid, data):
    text = data.get('text')
    if text:
        await manager.append_to_story(sid, text)
    else:
        await sio.emit("error", {"message": "Text cannot be empty"}, room=sid)

@sio.event
async def leave(sid, data):
    await manager.leave_room(sid)
    await sio.emit("left_room", {"message": "You have left the room."}, room=sid)

@sio.event
async def list_rooms(sid, data):
    rooms = manager.get_all_rooms()
    await sio.emit("rooms_list", {"rooms": rooms}, room=sid)
    print(f"Sent list of rooms to SID '{sid}': {rooms}")

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(sio_app, host="0.0.0.0", port=8000)
