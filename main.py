from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

import threading
import pics


class Root(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        self.label = Label(
            text="IRIS Pics\nReady",
            halign="center"
        )
        self.add_widget(self.label)

        run_btn = Button(
            text="Run Processor",
            size_hint=(1, 0.3)
        )
        run_btn.bind(on_press=self.run_pics)
        self.add_widget(run_btn)

    def run_pics(self, *args):
        self.label.text = "Running..."
        threading.Thread(target=self._run).start()

    def _run(self):
        try:
            pics.main()
            self.label.text = "Done"
        except Exception as e:
            self.label.text = f"Error:\n{e}"


class IrisApp(App):
    def build(self):
        return Root()


if __name__ == "__main__":
    IrisApp().run()
