# main.py
# Minimal Kivy GUI wrapper for pics.py
# DOES NOT modify pics.py

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.clock import Clock

import pics  # your existing logic


class MainUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=10, spacing=10, **kwargs)

        self.selected_path = ""

        # --- Folder selection ---
        self.path_input = TextInput(
            hint_text="Select folder...",
            multiline=False,
            readonly=True,
            size_hint_y=None,
            height=40,
        )
        self.add_widget(self.path_input)

        pick_btn = Button(text="Choose Folder", size_hint_y=None, height=40)
        pick_btn.bind(on_press=self.open_filechooser)
        self.add_widget(pick_btn)

        # --- Output format ---
        self.format_spinner = Spinner(
            text="keep",
            values=("keep", "jpg", "png", "webp"),
            size_hint_y=None,
            height=40,
        )
        self.add_widget(Label(text="Output format"))
        self.add_widget(self.format_spinner)

        # --- Quality ---
        self.quality_input = TextInput(
            text="85",
            multiline=False,
            input_filter="int",
            size_hint_y=None,
            height=40,
        )
        self.add_widget(Label(text="Quality (0–100)"))
        self.add_widget(self.quality_input)

        # --- Options ---
        self.recursive_chk = CheckBox()
        self.delete_chk = CheckBox()

        opt1 = BoxLayout(size_hint_y=None, height=30)
        opt1.add_widget(self.recursive_chk)
        opt1.add_widget(Label(text="Recursive"))
        self.add_widget(opt1)

        opt2 = BoxLayout(size_hint_y=None, height=30)
        opt2.add_widget(self.delete_chk)
        opt2.add_widget(Label(text="Delete originals"))
        self.add_widget(opt2)

        # --- Run button ---
        run_btn = Button(text="RUN", size_hint_y=None, height=50)
        run_btn.bind(on_press=self.run_pics)
        self.add_widget(run_btn)

        # --- Status ---
        self.status = Label(text="Idle")
        self.add_widget(self.status)

    def open_filechooser(self, instance):
        chooser = FileChooserListView(path=".", dirselect=True)

        popup = Popup(
            title="Select folder",
            content=chooser,
            size_hint=(0.9, 0.9),
        )

        def on_select(_, selection):
            if selection:
                self.selected_path = selection[0]
                self.path_input.text = self.selected_path
                popup.dismiss()

        chooser.bind(on_submit=on_select)
        popup.open()

    def run_pics(self, instance):
        if not self.selected_path:
            self.status.text = "ERROR: No folder selected"
            return

        try:
            quality = int(self.quality_input.text)
        except ValueError:
            self.status.text = "ERROR: Invalid quality"
            return

        self.status.text = "Running..."
        Clock.schedule_once(lambda dt: self._run_worker(quality), 0)

    def _run_worker(self, quality):
        try:
            # Call pics logic directly
            summary = pics.run_folder_mode(
                input_dir=self.selected_path,
                output_fmt=self.format_spinner.text,
                quality=quality,
                delete_original_on_win=self.delete_chk.active,
                backup_dir=None,
                skip_if_marked=False,
                recursive=self.recursive_chk.active,
            )
            self.status.text = "Done"
            print(summary)
        except Exception as e:
            self.status.text = f"ERROR: {e}"
            print(e)


class IRISPicsApp(App):
    def build(self):
        return MainUI()


if __name__ == "__main__":
    IRISPicsApp().run()
