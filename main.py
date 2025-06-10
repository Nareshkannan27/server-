import os
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import mainthread

from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import socket

# Android-specific imports
try:
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    android = True
except ImportError:
    android = False

PORT = 1234
httpd = None

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

class MyServerApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.output_label = Label(text='Choose a folder to serve.', size_hint_y=None, height=100)
        self.add_widget(self.output_label)

        self.choose_btn = Button(text='Choose Folder', size_hint_y=None, height=50)
        self.choose_btn.bind(on_press=self.choose_folder)
        self.add_widget(self.choose_btn)

        self.stop_btn = Button(text='Stop Server', size_hint_y=None, height=50, disabled=True)
        self.stop_btn.bind(on_press=self.stop_server)
        self.add_widget(self.stop_btn)

    def choose_folder(self, instance):
        chooser = FileChooserListView(path="/storage/emulated/0" if android else os.path.expanduser("~"))
        popup = Popup(title="Choose Folder", content=chooser, size_hint=(0.9, 0.9))

        def on_selection(*args):
            if chooser.selection:
                folder = chooser.selection[0]
                popup.dismiss()
                self.start_server(folder)

        chooser.bind(on_submit=on_selection)
        popup.open()

    @mainthread
    def update_label(self, text, color):
        self.output_label.text = text
        self.output_label.color = color

    def start_server(self, folder):
        global httpd
        os.chdir(folder)

        class SilentHandler(SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                return

        def server_thread():
            global httpd
            try:
                httpd = TCPServer(("", PORT), SilentHandler)
                ip = get_local_ip()
                self.update_label(f"Serving at http://{ip}:{PORT}\nFolder: {folder}", (0, 1, 0, 1))
                self.stop_btn.disabled = False
                self.choose_btn.disabled = True
                httpd.serve_forever()
            except Exception as e:
                self.update_label(f"Error: {e}", (1, 0, 0, 1))

        thread = threading.Thread(target=server_thread, daemon=True)
        thread.start()

    def stop_server(self, instance):
        global httpd
        if httpd:
            httpd.shutdown()
            httpd = None
            self.update_label("Server stopped.", (1, 0, 0, 1))
            self.choose_btn.disabled = False
            self.stop_btn.disabled = True

class ServerApp(App):
    def build(self):
        if android:
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])
        return MyServerApp()

if __name__ == '__main__':
    ServerApp().run()
