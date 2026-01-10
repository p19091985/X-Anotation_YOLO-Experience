import xml.etree.ElementTree as ET
import os

class LocalizationManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalizationManager, cls).__new__(cls)
            cls._instance.languages = {}
            cls._instance.current_language = 'pt_BR'
            cls._instance.load_languages()
        return cls._instance

    def load_languages(self):
        try:
            tree = ET.parse('languages.xml')
            root = tree.getroot()
            for lang in root.findall('language'):
                code = lang.get('code')
                name = lang.get('name')
                strings = {}
                for string in lang.findall('string'):
                    key = string.get('key')
                    value = string.text
                    strings[key] = value
                self.languages[code] = {'name': name, 'strings': strings}
                self.languages[code] = {'name': name, 'strings': strings}
        except Exception as e:
            print(f'Error loading languages: {e}')

    def reload_languages(self):
        self.languages = {}
        self.load_languages()

    def set_language(self, code):
        if code in self.languages:
            self.current_language = code

    def get_string(self, key):
        lang_data = self.languages.get(self.current_language)
        if lang_data and key in lang_data['strings']:
            return lang_data['strings'][key]
        pt_data = self.languages.get('pt_BR')
        if pt_data and key in pt_data['strings']:
            return pt_data['strings'][key]
        en_data = self.languages.get('en_US')
        if en_data and key in en_data['strings']:
            return en_data['strings'][key]
        return key

    def get_available_languages(self):
        return [(data['name'], code) for code, data in self.languages.items()]
_loc_manager = LocalizationManager()

def tr(key):
    return _loc_manager.get_string(key)

def reload():
    _loc_manager.reload_languages()

def set_language(code):
    _loc_manager.set_language(code)

def get_languages():
    return _loc_manager.get_available_languages()

def get_current_language():
    return _loc_manager.current_language