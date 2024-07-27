from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.clock import Clock
import requests


class MainApp(App):
    def __init__(self, **kwargs):
        super().__init__()
        self.width = None

    def build(self):
        self.data = {}
        self.long_press_time = 1  # Time in seconds to detect a long press

        layout = BoxLayout(orientation='vertical', spacing=5, padding=[10, 10])

        # Button to add data
        add_button = Button(text="Add item", size_hint=(1, 0.1))
        add_button.bind(on_release=self.show_add_popup)
        layout.add_widget(add_button)

        # Button to add new tab
        new_tab_button = Button(text="Add tab", size_hint=(1, 0.1))
        new_tab_button.bind(on_release=self.show_add_tab_popup)
        layout.add_widget(new_tab_button)

        # TabbedPanel
        self.tabbed_panel = TabbedPanel(do_default_tab=False)
        layout.add_widget(self.tabbed_panel)

        return layout

    def on_start(self):
        self.load_data()

    def load_data(self):
        try:
            response = requests.get('paste your api here')
            if response.status_code == 200:
                self.data = response.json()

                # Capitalize and sort data after loading
                self.data = {k.capitalize(): sorted(v, key=str.capitalize) for k, v in self.data.items()}

                self.display_tabs()
                print("Data downloaded:", self.data)
            else:
                self.display_error(f"Error {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            self.display_error(f"Error downloading data - {str(e)}")

    def display_tabs(self):
        # Save the current tab
        current_tab_text = self.tabbed_panel.current_tab.text if self.tabbed_panel.current_tab else None

        self.tabbed_panel.clear_tabs()
        for tab_name, tab_items in self.data.items():
            tab_content = BoxLayout(orientation='vertical', spacing=2, size_hint_y=None)
            tab_content.bind(minimum_height=tab_content.setter('height'))

            for item in tab_items:
                label = Label(
                    text=item,
                    size_hint_y=None,
                    text_size=(Window.width - 20, None),
                    height=Window.height / 20,
                    valign='middle',
                    halign='center'
                )
                label.bind(
                    size=lambda instance, value: setattr(instance, 'text_size', (instance.width, None))
                )
                label.bind(on_touch_down=self.on_item_touch_down)
                label.bind(on_touch_up=self.on_item_touch_up)
                tab_content.add_widget(label)

            scroll_view = ScrollView(size_hint=(1, 1))
            scroll_view.add_widget(tab_content)

            tab_item = TabbedPanelItem(text=tab_name)
            tab_item.content = scroll_view
            tab_item.bind(on_touch_down=self.show_rename_popup)
            self.tabbed_panel.add_widget(tab_item)

        # Restore the current tab
        if current_tab_text:
            for tab in self.tabbed_panel.tab_list:
                if tab.text == current_tab_text:
                    self.tabbed_panel.switch_to(tab)
                    break

    def show_add_popup(self, instance):
        self.popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        self.new_item_input = TextInput(hint_text="New item", multiline=False, size_hint=(1, 0.2))

        add_button = Button(text="Add", size_hint=(1, 0.2))
        add_button.bind(on_release=self.add_item)

        self.popup_layout.add_widget(self.new_item_input)
        self.popup_layout.add_widget(add_button)

        self.popup = Popup(title="Add a new item", content=self.popup_layout, size_hint=(0.75, 0.5))
        self.popup.open()

    def show_add_tab_popup(self, instance):
        self.popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        self.new_tab_input = TextInput(hint_text="Tab name", multiline=False, size_hint=(1, 0.2))

        add_button = Button(text="Add tab", size_hint=(1, 0.2))
        add_button.bind(on_release=self.add_tab)

        self.popup_layout.add_widget(self.new_tab_input)
        self.popup_layout.add_widget(add_button)

        self.popup = Popup(title="Add new tab", content=self.popup_layout, size_hint=(0.75, 0.5))
        self.popup.open()

    def add_item(self, instance):
        new_item = self.new_item_input.text.capitalize()
        current_tab = self.tabbed_panel.current_tab

        if new_item and current_tab:
            tab_name = current_tab.text
            self.popup.dismiss()

            print(f"Adding a new item: {new_item} to tab {tab_name}")

            if new_item.lower() in (item.lower() for item in self.data.get(tab_name, [])):
                self.display_error(f"Item '{new_item}' already exists in the tab '{tab_name}'")
                return

            if tab_name not in self.data:
                self.data[tab_name] = []
            self.data[tab_name].append(new_item)

            self.data[tab_name].sort(key=str.capitalize)

            self.send_data()

    def add_tab(self, instance):
        new_tab_name = self.new_tab_input.text.capitalize()

        if new_tab_name and new_tab_name.lower() not in (tab.lower() for tab in self.data.keys()):
            self.popup.dismiss()

            print(f"Adding a new tab: {new_tab_name}")

            # Update local data
            self.data[new_tab_name] = []

            self.data = dict(sorted(self.data.items()))

            self.send_data()

    def show_rename_popup(self, instance, touch):
        if instance.collide_point(*touch.pos) and touch.is_double_tap:
            self.popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

            self.rename_tab_input = TextInput(hint_text="New tab name", multiline=False, size_hint=(1, 0.2))
            self.old_tab_name = instance.text

            rename_button = Button(text="Change name", size_hint=(1, 0.2))
            rename_button.bind(on_release=self.rename_tab)

            delete_button = Button(text="Delete", size_hint=(1, 0.2))
            delete_button.bind(on_release=self.confirm_delete_tab)

            self.popup_layout.add_widget(self.rename_tab_input)
            self.popup_layout.add_widget(rename_button)
            self.popup_layout.add_widget(delete_button)

            self.popup = Popup(title="Tab options", content=self.popup_layout, size_hint=(0.75, 0.5))
            self.popup.open()

    def confirm_delete_tab(self, instance):
        self.popup.dismiss()

        self.popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        confirm_label = Label(text=f"Are you sure you want to delete the bookmark '{self.old_tab_name}'?")
        confirm_button = Button(text="Confirm", size_hint=(1, 0.2))
        confirm_button.bind(on_release=self.delete_tab)

        self.popup_layout.add_widget(confirm_label)
        self.popup_layout.add_widget(confirm_button)

        self.popup = Popup(title="Confirmation of bookmark deletion", content=self.popup_layout, size_hint=(0.75, 0.5))
        self.popup.open()

    def delete_tab(self, instance):
        tab_name = self.old_tab_name
        self.popup.dismiss()

        print(f"Deleting a bookmark: {tab_name}")

        # Update local data
        del self.data[tab_name]

        self.send_data()

    def rename_tab(self, instance):
        new_tab_name = self.rename_tab_input.text.capitalize()

        if new_tab_name and new_tab_name not in self.data:
            print(f"Renaming a tab from: {self.old_tab_name} to: {new_tab_name}")

            # Update local data
            self.data[new_tab_name] = self.data.pop(self.old_tab_name)

            self.data = dict(sorted(self.data.items()))

            self.send_data()

            self.popup.dismiss()

    def on_item_touch_down(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.touch_time = Clock.schedule_once(lambda dt: self.show_item_options(instance), self.long_press_time)

    def on_item_touch_up(self, instance, touch):
        if hasattr(self, 'touch_time') and self.touch_time:
            self.touch_time.cancel()

    def show_item_options(self, instance):
        self.popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        self.rename_item_input = TextInput(hint_text="New item name", multiline=False, size_hint=(1, 0.2))
        self.old_item_name = instance.text
        self.current_tab_name = self.tabbed_panel.current_tab.text
        rename_button = Button(text="Rename", size_hint=(1, 0.2))
        rename_button.bind(on_release=self.rename_item)

        delete_button = Button(text="Delete", size_hint=(1, 0.2))
        delete_button.bind(on_release=self.confirm_delete_item)

        self.popup_layout.add_widget(self.rename_item_input)
        self.popup_layout.add_widget(rename_button)
        self.popup_layout.add_widget(delete_button)

        self.popup = Popup(title="Position options", content=self.popup_layout, size_hint=(0.75, 0.5))
        self.popup.open()

    def confirm_delete_item(self, instance):
        self.popup.dismiss()

        self.popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        confirm_label = Label(text=f"Are you sure you want to delete the item? '{self.old_item_name}' from tab '{self.current_tab_name}'?")
        confirm_button = Button(text="Confirm", size_hint=(1, 0.2))
        confirm_button.bind(on_release=self.delete_item)

        self.popup_layout.add_widget(confirm_label)
        self.popup_layout.add_widget(confirm_button)

        self.popup = Popup(title="Confirmation of item deletion", content=self.popup_layout, size_hint=(0.75, 0.5))
        self.popup.open()

    def delete_item(self, instance):
        print(f"Deleting an item: {self.old_item_name} from the tab: {self.current_tab_name}")

        # Update local data
        self.data[self.current_tab_name].remove(self.old_item_name)

        self.send_data()

        self.popup.dismiss()

    def rename_item(self, instance):
        new_item_name = self.rename_item_input.text.capitalize()  # Capitalize new item name

        if new_item_name:
            print(f"Renaming an item from: {self.old_item_name} to: {new_item_name} in tab: {self.current_tab_name}")

            # Update local data
            self.data[self.current_tab_name] = [new_item_name if item == self.old_item_name else item for item in self.data[self.current_tab_name]]

            self.send_data()

            self.popup.dismiss()

    def send_data(self):
        try:
            response = requests.post('paste your api here', json=self.data)
            if response.status_code == 200:
                print("Data successfully sent to API")
                self.load_data()
            else:
                self.display_error(f"Error {response.status_code} - {response.text}")
        except requests.exceptions.RequestException as e:
            self.display_error(f"Error sending data - {str(e)}")

    def display_error(self, message):
        print("Error:", message)

if __name__ == '__main__':
    MainApp().run()
