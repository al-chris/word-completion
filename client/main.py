# client/main.py
import kivy
from kivy.app import App
from kivy.clock import mainthread
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.properties import StringProperty, ListProperty
from kivy.clock import mainthread
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.colorpicker import ColorPicker
import socketio
import uuid

kivy.require("2.1.0")

# Initialize Socket.IO client
sio = socketio.Client()

class LeftRoomPopup(Popup):
    pass

class DisconnectPopup(Popup):
    pass
class LoginScreen(Screen):
    def join_game(self):
        username = self.ids.username.text.strip()
        room = self.ids.room.text.strip()
        color = self.ids.color_picker_text.text.strip()  # Expecting a hex color code
        if username and room and color:
            app = App.get_running_app()
            if app.connected:
                app.username = username
                app.room = room
                app.user_color = color
                print(f"Username: {username}, Room: {room}, Color: {color}")
                try:
                    sio.emit("join", {"username": username, "room": room, "color": color})
                    app.root.current = "game"
                except Exception as e:
                    print(f"Failed to emit join event: {e}")
            else:
                print("Not connected to the server. Please try again later.")
        else:
            print("Username, Room, and Color are required")

    def go_to_search_rooms(self):
        # Navigate to the SearchRoomsScreen
        app = App.get_running_app()
        try:
            sio.emit("list_rooms", {})
            app.root.current = "search_rooms"
        except Exception as e:
            print(f"Failed to emit list_rooms event: {e}")

class SearchRoomsScreen(Screen):
    rooms = ListProperty([])

    def on_pre_enter(self):
        # Clear existing rooms list
        self.rooms = []
        rooms_layout = self.ids.rooms_layout
        rooms_layout.clear_widgets()

    @mainthread
    def populate_rooms(self, rooms):
        self.rooms = rooms
        rooms_layout = self.ids.rooms_layout
        rooms_layout.clear_widgets()
        for room in rooms:
            btn = Button(text=room, size_hint_y=None, height='40dp')
            btn.bind(on_press=lambda instance, room_name=room: self.select_room(room_name))
            rooms_layout.add_widget(btn)

    def select_room(self, room_name):
        # Navigate back to LoginScreen with the selected room name
        app = App.get_running_app()
        login_screen = app.root.get_screen("login")
        login_screen.ids.room.text = room_name
        app.root.current = "login"

class GameScreen(Screen):
    board = StringProperty("")
    users = ListProperty([])
    current_turn = StringProperty("")  # New property to track whose turn it is

    def send_text(self):
        if self.current_turn != App.get_running_app().username:
            print("It's not your turn.")
            return
        text = self.ids.text_input.text.strip()
        if text:
            app = App.get_running_app()
            if app.connected:
                try:
                    sio.emit("send_text", {"text": text})
                    self.ids.text_input.text = ""
                except Exception as e:
                    print(f"Failed to emit send_text event: {e}")
            else:
                print("Not connected to the server. Please try again later.")
        else:
            print("Cannot send empty text")

    def leave_room(self):
        app = App.get_running_app()
        if app.connected:
            try:
                sio.emit("leave", {})
                app.root.current = "login"
                # Optionally, clear user data
                app.username = ""
                app.room = ""
                app.user_color = "#000000"
                self.board = ""
                self.users = []
            except Exception as e:
                print(f"Failed to emit leave event: {e}")
        else:
            print("Not connected to the server.")

class WindowManager(ScreenManager):
    pass

class ColorPickerPopup(Popup):
    pass

class WordCompletionApp(App):
    username = StringProperty("")
    room = StringProperty("")
    user_color = StringProperty("#000000")  # Default color
    connected = False  # Flag to track connection status

    def build(self):
        # Register Socket.IO event handlers
        sio.on("connect", self.on_connect)
        sio.on("disconnect", self.on_disconnect)
        sio.on("joined", self.on_joined)
        sio.on("update_story", self.on_update_story)
        sio.on("user_joined", self.on_user_joined)
        sio.on("user_left", self.on_user_left)
        sio.on("room_created", self.on_room_created)
        sio.on("rooms_list", self.on_rooms_list)
        sio.on("turn_update", self.on_turn_update)  # Register turn_update handler
        sio.on("error", self.on_error)
        sio.on("left_room", self.on_left_room)

        # Connect to the server
        try:
            sio.connect("http://localhost:8000", wait_timeout=15)
            print("Attempting to connect to the server...")
        except Exception as e:
            print(f"Connection failed: {e}")

        return Builder.load_file("game.kv")

    def on_connect(self):
        self.connected = True
        print("Successfully connected to the server.")

    def on_disconnect(self):
        self.connected = False
        print("Disconnected from the server.")
        self.show_disconnect_popup()

    def on_joined(self, data):
        print(f"Joined successfully with UID: {data['uid']}")

    def on_update_story(self, data):
        story = data.get('story', '')
        self.root.get_screen("game").board = story
        print("Story updated.")

    def on_turn_update(self, data):
        current_turn = data.get('current_turn', '')
        game_screen = self.root.get_screen("game")
        game_screen.current_turn = current_turn
        if current_turn == self.username:
            game_screen.ids.text_input.disabled = False
            game_screen.ids.send_button.disabled = False
        else:
            game_screen.ids.text_input.disabled = True
            game_screen.ids.send_button.disabled = True
        # Optionally, display a message
        print(f"It's now {current_turn}'s turn.")

    @mainthread
    def on_user_joined(self, data):
        uid = data.get('uid')
        username = data.get('username')
        user_entry = f"{username} ({uid})"
        if user_entry not in self.root.get_screen("game").users:
            self.root.get_screen("game").users.append(user_entry)
        print(f"User '{username}' has joined the room.")

    def on_user_left(self, data):
        uid = data.get('uid')
        username = data.get('username')
        user_entry = f"{username} ({uid})"
        if user_entry in self.root.get_screen("game").users:
            self.root.get_screen("game").users.remove(user_entry)
        print(f"User '{username}' has left the room.")

    def on_rooms_list(self, data):
        rooms = data.get('rooms', [])
        search_rooms_screen = self.root.get_screen("search_rooms")
        search_rooms_screen.populate_rooms(rooms)
        print(f"Received rooms list: {rooms}")

    def on_room_created(self, data):
        room = data.get('room')
        print(f"Room created: {room}")

    def on_error(self, data):
        message = data.get('message', 'An error occurred')
        print(f"Error: {message}")

    def on_left_room(self, data):
        message = data.get('message', 'Left the room successfully.')
        print(message)
        self.show_left_room_popup(message)

    def on_stop(self):
        if self.connected:
            sio.disconnect()
            print("Disconnected from the server upon app stop.")

    # Methods for Color Picker
    def show_color_picker(self):
        popup = ColorPickerPopup()
        popup.open()

    def select_color(self, color_tuple):
        # Convert RGBA tuple to hex color
        hex_color = '#{:02X}{:02X}{:02X}'.format(
            int(color_tuple[0]*255),
            int(color_tuple[1]*255),
            int(color_tuple[2]*255)
        )
        # Simple validation to check if it's a valid hex color
        if len(hex_color) == 7 and hex_color.startswith('#'):
            login_screen = self.root.get_screen("login")
            login_screen.ids.color_picker_text.text = hex_color
            print(f"Selected color: {hex_color}")
        else:
            print("Invalid color selected.")
    
    @mainthread
    def show_left_room_popup(self, message):
        popup = LeftRoomPopup()
        popup.open()

    @mainthread
    def show_disconnect_popup(self):
        popup = DisconnectPopup()
        popup.open()

if __name__ == "__main__":
    WordCompletionApp().run()
