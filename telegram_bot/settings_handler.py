import json
from pathlib import Path

script_dir = Path(__file__).parent
USER_SETTINGS_FILE = script_dir / "user_settings.json"
TRANSLATION_FILE = script_dir / "translations.json"

class Settings:
    def __init__(self):
        # Load user languages from file
        # Format: {user_id: {lang_code: lang_code, temp_unit: unit}}
        self.user_settings = self._load_user_settings()
        # Load translations from file
        # Format: {lang_code: {key: translation}}
        self.translations = self._load_translations()

    def _load_user_settings(self, filepath=USER_SETTINGS_FILE):
        if filepath.exists():
            with filepath.open("r", encoding="utf-8") as file:
                return json.load(file)
        return {}
    
    def _load_translations(self, filepath=TRANSLATION_FILE):
        if filepath.exists():
            with filepath.open("r", encoding="utf-8") as file:
                return json.load(file)
        return {}

    def refresh_user_settings(self):
        self.user_settings = self._load_user_settings()

    def save_user_settings(self, settings, filepath=USER_SETTINGS_FILE):
        with filepath.open("w", encoding="utf-8") as file:
            json.dump(settings, file)

    def set_user_language(self, user_id: str, lang_code: str):
        self.refresh_user_settings()
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {}
        self.user_settings[user_id]['lang_code'] = lang_code
        self.save_user_settings(self.user_settings)

    def get_user_language(self, user_id: str, default: str = "en") -> str:
        self.refresh_user_settings()
        return self.user_settings.get(user_id, {}).get('lang_code', default)

    def set_user_temp_unit(self, user_id: str, unit: str):
        self.refresh_user_settings()
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {}
        self.user_settings[user_id]['temp_unit'] = unit
        self.save_user_settings(self.user_settings)

    def get_user_temp_unit(self, user_id: str, default: str = "C") -> str:
        self.refresh_user_settings()
        return self.user_settings.get(user_id, {}).get('temp_unit', default)

    def get_translation(self, lang_code: str, key: str, default: str = 'Translation file missing!', **kwargs) -> str:
        message = self.translations.get(lang_code, {}).get(key, default)
        if kwargs:
            # Only format if there are placeholders to replace.
            try:
                return message.format(**kwargs)
            except (KeyError, IndexError):
                return f"⚠️ Missing placeholder in translation: {message}"
        else:
            return message



