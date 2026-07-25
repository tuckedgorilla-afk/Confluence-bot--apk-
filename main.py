from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from android import AndroidService

class ConfluenceBotApp(App):
    def build(self):
        self.service = None
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        self.label = Label(
            text="Confluence Engine: STOPPED", 
            font_size='18sp',
            halign='center'
        )
        layout.add_widget(self.label)
        
        self.btn = ToggleButton(
            text='START SCANNER', 
            font_size='20sp',
            size_hint=(1, 0.3)
        )
        self.btn.bind(on_press=self.toggle_service)
        layout.add_widget(self.btn)
        
        return layout

    def toggle_service(self, instance):
        if instance.state == 'down':
            self.start_service()
            self.label.text = "Confluence Engine: RUNNING 🚀"
            instance.text = "STOP SCANNER"
        else:
            self.stop_service()
            self.label.text = "Confluence Engine: STOPPED"
            instance.text = "START SCANNER"

    def start_service(self):
        self.service = AndroidService('Confluence Engine', 'Scanning Binance Futures...')
        self.service.start('service started')

    def stop_service(self):
        if self.service:
            self.service.stop()

if __name__ == '__main__':
    ConfluenceBotApp().run()
