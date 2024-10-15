# client/main.py
import os
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.pickers import MDColorPicker
from kivymd.uix.menu import MDDropdownMenu
from kivymd.toast import toast
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.config import Config
from kivy.properties import StringProperty, ListProperty
import socketio

# Don't use env files (didn't work for me)

# Window.size = (300,648)
# Config.set('graphics', 'resizable', False)
Window.softinput_mode = "below_target"
Config.set('kivy','window_icon','word_comp_logo.ico')
API_URL = "https://word-completion-bcih.onrender.com"
# Initialize Socket.IO client
sio = socketio.Client()

class LeftRoomDialog(MDDialog):
    pass

class DisconnectDialog(MDDialog):
    pass

class LoginScreen(MDScreen):
    def join_game(self):
        username = self.ids.username.text.strip()
        room = self.ids.room.text.strip()
        color = self.ids.color_picker_text.text.strip()  # Expecting a hex color code
        if username and room and color:
            app = MDApp.get_running_app()
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
        app = MDApp.get_running_app()
        try:
            sio.emit("list_rooms", {})
            app.root.current = "search_rooms"
        except Exception as e:
            print(f"Failed to emit list_rooms event: {e}")

class SearchRoomsScreen(MDScreen):
    rooms = ListProperty([])

    def on_pre_enter(self):
        self.rooms = []
        rooms_layout = self.ids.rooms_layout
        rooms_layout.clear_widgets()

    @mainthread
    def populate_rooms(self, rooms):
        self.rooms = rooms
        rooms_layout = self.ids.rooms_layout
        rooms_layout.clear_widgets()
        for room in rooms:
            btn = MDRaisedButton(text=room, size_hint=(0.55, 1), height='40dp')
            btn.bind(on_release=lambda instance, room_name=room: self.select_room(room_name))
            rooms_layout.add_widget(btn)

    def select_room(self, room_name):
        app = MDApp.get_running_app()
        login_screen = app.root.get_screen("login")
        login_screen.ids.room.text = room_name
        app.root.current = "login"

class GameScreen(MDScreen):
    board = StringProperty("")
    users = ListProperty([])
    current_turn = StringProperty("")

    def on_kv_post(self, base_widget):
        self.caller = self.ids.caller
        
    def drop(self):
        get_before_paren = lambda s: s.split('(')[0]
        self.dropdown = MDDropdownMenu(
            caller=self.caller, 
            items=[
                {
                    "viewclass": "OneLineListItem", 
                    "text": get_before_paren(user)
                } for user in self.users
            ], 
            width_mult=4
        )
        self.dropdown.open()

    def send_text(self):
        if self.current_turn != MDApp.get_running_app().username:
            print("It's not your turn.")
            return
        text = self.ids.text_input.text.strip()
        if text:
            app = MDApp.get_running_app()
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
        app = MDApp.get_running_app()
        if app.connected:
            try:
                sio.emit("leave", {})
                app.root.current = "login"
                app.username = ""
                app.room = ""
                app.user_color = "#000000"
                self.board = ""
                self.users = []
            except Exception as e:
                print(f"Failed to emit leave event: {e}")
        else:
            print("Not connected to the server.")

class WordCompletionApp(MDApp):
    username = StringProperty("")
    room = StringProperty("")
    user_color = StringProperty("#000000")
    connected = False

    def build(self):
        self.icon = "word_comp_logo.ico"
        self.color_picker = MDColorPicker(size_hint=(0.45, 0.85))
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.accent_palette = "Teal"
        self.theme_cls.theme_style = "Light"

        # Register Socket.IO event handlers
        sio.on("connect", self.on_connect)
        sio.on("disconnect", self.on_disconnect)
        sio.on("joined", self.on_joined)
        sio.on("update_story", self.on_update_story)
        sio.on("user_joined", self.on_user_joined)
        sio.on("user_left", self.on_user_left)
        sio.on("room_created", self.on_room_created)
        sio.on("rooms_list", self.on_rooms_list)
        sio.on("turn_update", self.on_turn_update)
        sio.on("error", self.on_error)
        sio.on("left_room", self.on_left_room)

        # Connect to the server
        try:
            sio.connect(API_URL, wait_timeout=120)
            print("Attempting to connect to the server...")
        except Exception as e:
            print(f"Connection failed: {e}")

        return Builder.load_file("game.kv")
    
    def on_start(self):
        self.fps_monitor_start()
    
    def toggle_theme(self, instance, value):
        self.theme_cls.theme_style = "Dark" if value else "Light"

    def on_connect(self):
        self.connected = True
        print("Successfully connected to the server.")

    def on_disconnect(self):
        self.connected = False
        print("Disconnected from the server.")
        self.show_disconnect_dialog()

    def on_joined(self, data):
        user = self.username
        print(f"User '{user}' has joined the room.")
        if user not in self.root.get_screen("game").users:
            self.root.get_screen("game").users.append(user)
        print(f"Joined successfully with UID: {data['uid']}")
        toast(f"Joined successfully with UID: {data['uid']}")

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
        print(f"It's now {current_turn}'s turn.")

    @mainthread
    def on_user_joined(self, data):
        uid = data.get('uid')
        username = data.get('username')
        user_entry = f"{username} ({uid})"
        if user_entry not in self.root.get_screen("game").users:
            self.root.get_screen("game").users.append(user_entry)
        print(f"User '{username}' has joined the room.")
        toast(f"User '{username}' has joined the room.")

    def on_user_left(self, data):
        uid = data.get('uid')
        username = data.get('username')
        user_entry = f"{username} ({uid})"
        if user_entry in self.root.get_screen("game").users:
            self.root.get_screen("game").users.remove(user_entry)
        print(f"User '{username}' has left the room.")
        toast(f"User '{username}' has left the room.")

    def on_rooms_list(self, data):
        rooms = data.get('rooms', [])
        search_rooms_screen = self.root.get_screen("search_rooms")
        search_rooms_screen.populate_rooms(rooms)
        print(f"Received rooms list: {rooms}")

    def on_room_created(self, data):
        room = data.get('room')
        print(f"Room created: {room}")
        toast(f"Room created: {room}")

    def on_error(self, data):
        message = data.get('message', 'An error occurred')
        print(f"Error: {message}")

    def on_left_room(self, data):
        message = data.get('message', 'Left the room successfully.')
        print(message)
        self.show_left_room_dialog(message)

    def on_stop(self):
        if self.connected:
            sio.disconnect()
            print("Disconnected from the server upon app stop.")

    def show_color_picker(self):
        self.color_picker.open()
        self.color_picker.bind(
            on_select_color=self.on_select_color,
            on_release=self.get_selected_color,
        )

    def on_select_color(self, instance_gradient_tab, color: list) -> None:
        # Convert the color to hex format
        hex_color = '#{:02X}{:02X}{:02X}'.format(
            int(color[0]*255),
            int(color[1]*255),
            int(color[2]*255)
        )
        
        # Update the color in the UI
        login_screen = self.root.get_screen("login")
        login_screen.ids.color_picker_text.text = hex_color
        
        # Update the user_color property
        self.user_color = hex_color
        
        # Close the color picker
        if self.color_picker:
            self.color_picker.dismiss()
        
        print(f"Selected color: {hex_color}")
        toast(f"Selected color: {hex_color}")

    def get_selected_color(self, instance_color_picker, type_color, selected_color):
        # hex_color = '#{:02X}{:02X}{:02X}'.format(
        #     int(selected_color[0]*255),
        #     int(selected_color[1]*255),
        #     int(selected_color[2]*255)
        # )
        # login_screen = self.root.get_screen("login")
        # login_screen.ids.color_picker_text.text = hex_color
        # print(f"Selected color: {hex_color}")
        # toast(f"Selected color: {hex_color}")

        pass

    @mainthread
    def show_left_room_dialog(self, message):
        dialog = LeftRoomDialog(
            text="You have left the room.",
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    @mainthread
    def show_disconnect_dialog(self):
        dialog = DisconnectDialog(
            text="You have been disconnected from the server.",
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

if __name__ == "__main__":
    WordCompletionApp().run()
