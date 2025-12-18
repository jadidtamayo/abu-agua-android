from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import OneLineListItem
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from kivy.metrics import dp

import threading
import os
from datetime import datetime, timezone

# Import local modules
# Since we are in the same dir on Android
import sistemas
import telegram_service
import message_parser

class ConfigScreen(MDScreen):
    pass

class InfraItem(OneLineListItem):
    # Custom item to ensure text size is large enough
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.output_text = "body1"
        self._txt_bot_pad = dp(20) # Add padding
        self.height = dp(60) # Taller height

class DashboardScreen(MDScreen):
    info_text = StringProperty("Cargando...")
    pub_date = StringProperty("")
    text_date = StringProperty("")

class AbuAguaApp(MDApp):
    # Valid KivyMD attributes
    selected_infra_full = StringProperty("")
    
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        
        # Persistence
        # Store in user data dir
        store_path = os.path.join(self.user_data_dir, 'app_config.json')
        self.store = JsonStore(store_path)
        
        sm = MDScreenManager()
        sm.add_widget(ConfigScreen(name='config'))
        sm.add_widget(DashboardScreen(name='dashboard'))
        return sm

    def on_start(self):
        # Populate the list
        self.flattened_infra = []
        for sys_name, infra_list in sistemas.SISTEMAS.items():
            for infra_name in infra_list:
                full_name = f"{sys_name} - {infra_name}"
                self.flattened_infra.append(full_name)
        
        # Get list widget
        config_screen = self.root.get_screen('config')
        infra_list_widget = config_screen.ids.infra_list_view
        
        for infra in self.flattened_infra:
            item = InfraItem(text=infra)
            # Bind release event
            item.bind(on_release=lambda x, i=infra: self.set_infra(i))
            infra_list_widget.add_widget(item)

        # Check existing config
        if self.store.exists('config'):
            saved_infra = self.store.get('config')['infra']
            self.selected_infra_full = saved_infra
            self.root.current = 'dashboard'
            self.refresh_data()
        else:
            self.root.current = 'config'

    def set_infra(self, text_item):
        self.selected_infra_full = text_item
        # Save
        self.store.put('config', infra=text_item)
        # Go to Dashboard and refresh
        self.root.current = 'dashboard'
        self.refresh_data()

    def reset_config(self):
        self.root.current = 'config'

    def refresh_data(self):
        screen = self.root.get_screen('dashboard')
        screen.info_text = "Buscando información..."
        screen.pub_date = ""
        screen.text_date = ""
        
        threading.Thread(target=self.fetch_background).start()

    def fetch_background(self):
        try:
            if " - " not in self.selected_infra_full:
                self.update_ui_error("Configuración inválida")
                return

            system_part, infra_part = self.selected_infra_full.split(" - ", 1)
            
            # Helper for flexible matching
            def normalize_name(name):
                # Lowercase, remove "de ", "del ", strip spaces
                n = name.lower()
                n = n.replace(" de ", " ")
                n = n.replace(" del ", " ")
                return n.strip()

            target_infra_norm = normalize_name(infra_part)
            
            msgs = telegram_service.get_last_messages(n=15)
            found = False
            
            # Filter phrase
            filter_phrase = "estimado cliente a continuacion la distribucion del servicio de agua para la jornada"
            
            for msg_data in reversed(msgs):
                text = msg_data['text']
                
                # Check filter phrase (flexible spaces/case)
                clean_text_check = text.lower().replace("\n", " ").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
                filter_phrase_norm = filter_phrase.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

                if filter_phrase_norm not in clean_text_check:
                     continue
                
                pub_date = msg_data['datetime']
                
                parsed = message_parser.parse_water_distribution(text)
                date_in_text = parsed.get("date", "Desconocida")
                
                for seg in parsed.get("segments", []):
                    seg_infra = seg.get("infraestructura", "")
                    seg_infra_norm = normalize_name(seg_infra)
                    
                    if target_infra_norm in seg_infra_norm or seg_infra_norm in target_infra_norm:
                        found = True
                        original_note = seg.get("nota_original", "")
                        text_display = f"Infraestructura: {seg_infra}\n\nNota: {original_note}"
                        Clock.schedule_once(lambda dt: self.update_ui_success(text_display, pub_date, date_in_text))
                        return

            if not found:
                Clock.schedule_once(lambda dt: self.update_ui_error("No se encontró información reciente para esta infraestructura."))

        except Exception as e:
            err_msg = str(e)
            Clock.schedule_once(lambda dt: self.update_ui_error(f"Error: {err_msg}"))

    def update_ui_success(self, text, pub_date, text_date):
        screen = self.root.get_screen('dashboard')
        screen.info_text = text
        
        friendly_date = "Desconocido"
        if pub_date:
            try:
                # Parse ISO format (handles 2025-12-18T00:24:09+00:00)
                dt = datetime.fromisoformat(pub_date)
                # Convert to local time (system time)
                dt_local = dt.astimezone()
                # Format: 18-12-2025 9:00 AM
                friendly_date = dt_local.strftime("%d-%m-%Y %I:%M %p")
            except Exception as e:
                friendly_date = pub_date # Fallback

        screen.pub_date = f"Publicado: {friendly_date}"
        screen.text_date = f"Para el día: {text_date}"

    def update_ui_error(self, error_msg):
        screen = self.root.get_screen('dashboard')
        screen.info_text = error_msg

from kivy.lang import Builder
Builder.load_string('''
<ConfigScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(10)
        
        MDLabel:
            text: "Seleccione su infraestructura"
            halign: "center"
            theme_text_color: "Primary"
            font_style: "H5"
            size_hint_y: None
            height: dp(60)

        # List container
        MDCard:
            orientation: 'vertical'
            padding: 0
            radius: [10]
            elevation: 2
            
            ScrollView:
                MDList:
                    id: infra_list_view
<DashboardScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        
        MDTopAppBar:
            title: "AbuAgua"
            right_action_items: [["cog", lambda x: app.reset_config()], ["refresh", lambda x: app.refresh_data()]]
            elevation: 4

        ScrollView:
            MDBoxLayout:
                orientation: 'vertical'
                padding: dp(20)
                spacing: dp(20)
                adaptive_height: True

                MDCard:
                    orientation: 'vertical'
                    padding: dp(20)
                    spacing: dp(15)
                    size_hint_y: None
                    height: self.minimum_height
                    radius: [15]
                    elevation: 3

                    MDLabel:
                        text: root.text_date
                        font_style: "H5"
                        bold: True
                        theme_text_color: "Primary"
                        size_hint_y: None
                        height: self.texture_size[1]
                        
                    MDLabel:
                        text: root.pub_date
                        font_style: "Body1"
                        theme_text_color: "Secondary"
                        size_hint_y: None
                        height: self.texture_size[1]
                    
                    MDSeparator:
                        height: dp(2)

                    MDLabel:
                        text: root.info_text
                        font_style: "H6"
                        theme_text_color: "Primary"
                        size_hint_y: None
                        height: self.texture_size[1]
                        markup: True
                        line_height: 1.4
''')

if __name__ == "__main__":
    AbuAguaApp().run()
