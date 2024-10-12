# from kivymd.app import MDApp
# from kivy.factory import Factory
# from kivy.lang import Builder

# from kivymd.theming import ThemeManager

# Builder.load_string(
#     '''
# #:import toast kivymd.toast.toast


# <MyRoot@BoxLayout>
#     orientation: 'vertical'

#     MDTopAppBar:
#         title: "Test MDDropDownItem"
#         md_bg_color: app.theme_cls.primary_color
#         elevation: 10
#         left_action_items: [['menu', lambda x: x]]

#     FloatLayout:

#         MDDropDownItem:
#             id: dropdown_item
#             pos_hint: {'center_x': 0.5, 'center_y': 0.6}
#             items: app.items
#             dropdown_bg: [1, 1, 1, 1]

#         MDRaisedButton:
#             pos_hint: {'center_x': 0.5, 'center_y': 0.3}
#             text: 'Chek Item'
#             on_release: toast(dropdown_item.current_item)
# ''')


# class Test(MDApp):

#     def build(self):
#         self.items = [f"Item {i}" for i in range(50)]
#         return Factory.MyRoot()


# Test().run()



# from kivymd.app import MDApp
# from kivymd.uix.menu import MDDropdownMenu

# from kivy.properties import StringProperty
# from kivy.lang import Builder

# KV = """
# Screen:
#     MDTextField:
#         id: fahrenheit
#         hint_text:"Enter Fahrenheit"
#         helper_text: "Once you enter the fahrenheit the press submit"
#         helper_text_mode: "on_focus"
#         icon_right: "temperature-fahrenheit"
#         pos_hint: {'center_x': 0.5, 'center_y': 0.9}
#         size: 200, 25
#         size_hint: None, None

#     MDRoundFlatButton:
#         text: "Enter"
#         pos_hint: {'center': (0.5,0.2)}
#         text_color: 0, 1, 0, 1
#         size_hint: 0.25, 0.20
#         on_release: app.show_data()

#     MDIconButton:
#         id: button
#         icon: "language-python"
#         pos_hint: {"center_x": .5, "center_y": .5}
#         on_release: app.dropdown1.open()
# """


# class DemoApp(MDApp):

#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.screen = Builder.load_string(KV)

#         menu_items = [
#             {
#                 "viewclass": "OneLineListItem",
#                 "text": "Option1",
#                 "on_release": lambda *args: self.callback()
#             },
#             {
#                 "viewclass": "OneLineListItem",
#                 "text": "Option2",
#                 "on_release": lambda *args: self.callback()
#             },
#             {
#                 "viewclass": "OneLineListItem",
#                 "text": "Option3",
#                 "on_release": lambda *args: self.callback()
#             }
#         ]

#         self.dropdown1 = MDDropdownMenu(items=menu_items, width_mult=4, caller=self.screen.ids.button)

#     def build(self):
#         return self.screen

#     def show_data(self):
#         input_fahrenheit = self.root.ids.fahrenheit.text
#         print(input_fahrenheit)

#     @staticmethod
#     def callback():
#         print("cookies")


# DemoApp().run()


# from kivy.lang import Builder

# from kivymd.app import MDApp
# from kivymd.toast import toast

# KV = '''
# MDScreen:

#     MDTopAppBar:
#         title: 'Test Toast'
#         pos_hint: {'top': 1}
#         left_action_items: [['menu', lambda x: x]]

#     MDRaisedButton:
#         text: 'TEST KIVY TOAST'
#         pos_hint: {'center_x': .5, 'center_y': .5}
#         on_release: app.show_toast()
# '''


# class Test(MDApp):
#     def show_toast(self):
#         '''Displays a toast on the screen.'''

#         toast('Test Kivy Toast')

#     def build(self):
#         return Builder.load_string(KV)

# Test().run()


# from kivy.lang import Builder
# from kivy.properties import StringProperty

# from kivymd.app import MDApp
# from kivymd.uix.card import MDCard

# KV = '''
# <MD3Card>
#     padding: 4
#     size_hint: None, None
#     size: "200dp", "100dp"

#     MDRelativeLayout:

#         MDIconButton:
#             icon: "dots-vertical"
#             pos_hint: {"top": 1, "right": 1}

#         MDLabel:
#             id: label
#             text: root.text
#             adaptive_size: True
#             color: "grey"
#             pos: "12dp", "12dp"
#             bold: True


# MDScreen:

#     MDBoxLayout:
#         id: box
#         adaptive_size: True
#         spacing: "56dp"
#         pos_hint: {"center_x": .5, "center_y": .5}
# '''


# class MD3Card(MDCard):
#     '''Implements a material design v3 card.'''

#     text = StringProperty()


# class Example(MDApp):
#     def build(self):
#         self.theme_cls.material_style = "M3"
#         return Builder.load_string(KV)

#     def on_start(self):
#         styles = {
#             "elevated": "#f6eeee", "filled": "#f4dedc", "outlined": "#f8f5f4"
#         }
#         for style in styles.keys():
#             self.root.ids.box.add_widget(
#                 MD3Card(
#                     line_color=(0.2, 0.2, 0.2, 0.8),
#                     style=style,
#                     text=style.capitalize(),
#                     md_bg_color=styles[style],
#                     shadow_softness=2 if style == "elevated" else 12,
#                     shadow_offset=(0, 1) if style == "elevated" else (0, 2),
#                 )
#             )


# Example().run()


from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen

from kivymd.icon_definitions import md_icons
from kivymd.app import MDApp
from kivymd.uix.list import OneLineIconListItem


Builder.load_string(
    '''
#:import images_path kivymd.images_path


<CustomOneLineIconListItem>

    IconLeftWidget:
        icon: root.icon


<PreviousMDIcons>

    MDBoxLayout:
        orientation: 'vertical'
        spacing: dp(10)
        padding: dp(20)

        MDBoxLayout:
            adaptive_height: True

            MDIconButton:
                icon: 'magnify'

            MDTextField:
                id: search_field
                hint_text: 'Search icon'
                on_text: root.set_list_md_icons(self.text, True)

        RecycleView:
            id: rv
            key_viewclass: 'viewclass'
            key_size: 'height'

            RecycleBoxLayout:
                padding: dp(10)
                default_size: None, dp(48)
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: 'vertical'
'''
)


class CustomOneLineIconListItem(OneLineIconListItem):
    icon = StringProperty()


class PreviousMDIcons(Screen):

    def set_list_md_icons(self, text="", search=False):
        '''Builds a list of icons for the screen MDIcons.'''

        def add_icon_item(name_icon):
            self.ids.rv.data.append(
                {
                    "viewclass": "CustomOneLineIconListItem",
                    "icon": name_icon,
                    "text": name_icon,
                    "callback": lambda x: x,
                }
            )

        self.ids.rv.data = []
        for name_icon in md_icons.keys():
            if search:
                if text in name_icon:
                    add_icon_item(name_icon)
            else:
                add_icon_item(name_icon)


class MainApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.screen = PreviousMDIcons()

    def build(self):
        return self.screen

    def on_start(self):
        self.screen.set_list_md_icons()


MainApp().run()