#!/usr/bin/env python3
"""
Settings Manager

Centrale configuratie voor het hele chess project.
Beheert persistente instellingen via JSON file storage.

Instellingen:
- show_coordinates: Toon A-H/1-8 randen op bord (bool)
- debug_sensors: Enable sensor detection overlay (bool)
- vs_computer: Speel tegen Stockfish AI (bool)
- stockfish_skill_level: AI moeilijkheid 0-20 (int)
- stockfish_think_time: Denktijd per zet in ms (int)
- stockfish_depth: Maximale zoekdiepte (int)
- stockfish_threads: Aantal CPU threads (int)
- led_brightness: LED helderheid 0-100 (int)

Functionaliteit:
- Lazy loading: settings.json wordt alleen geladen bij eerste access
- Auto-save: save() schrijft wijzigingen terug naar disk
- Default values: Als settings.json niet bestaat, gebruik defaults
- Singleton pattern via global Settings() instance

File locatie: settings.json in project root directory

Wordt gebruikt door: Alle modules die configuratie nodig hebben
"""

import json
import os


class Settings:
    """Beheert applicatie instellingen"""
    
    # LED Power calibration data (brightness % -> Ampere)
    POWER_CALIBRATION = {
        1: 0.05, 2: 0.08, 3: 0.10, 4: 0.13, 5: 0.14,
        6: 0.17, 7: 0.19, 8: 0.22, 9: 0.24, 10: 0.27,
        15: 0.40, 20: 0.52, 25: 0.64, 30: 0.76, 35: 0.89,
        40: 1.01, 45: 1.13, 50: 1.26, 55: 1.38, 60: 1.50,
        65: 1.62, 70: 1.74, 75: 1.87, 80: 1.99, 85: 2.10,
        90: 2.22, 95: 2.34, 100: 2.48
    }
    
    # Power profile presets (Ampere limit -> max brightness %)
    POWER_PROFILES = {
        0.5: 20,   # Low Power
        1.0: 40,   # Medium
        1.5: 60,   # Standard
        2.0: 80,   # High
        2.5: 100,  # Maximum
    }
    
    # Default settings (gestructureerd in secties)
    DEFAULTS = {
        'hardware': {
            'brightness': 20,
            'power_profile': 1.5,  # Power limit in Ampere (0.5, 1.0, 1.5, 2.0, 2.5)
        },
        'general': {
            'screensaver_audio': True,  # Muziek tijdens screensaver
        },
        'debug': {
            'show_coordinates': True,
            'debug_sensors': False,
            'validate_board_state': False,
        },
        'chess': {
            'play_vs_computer': False,
            'strict_touch_move': False,  # Touch-move regel
            'stockfish_skill_level': 10,  # 0-20 (0=zwakst, 20=sterkst)
            'stockfish_think_time': 1000,  # Denktijd in ms (500-10000)
            'stockfish_depth': 15,  # Maximale zoekdiepte (5-25)
            'stockfish_threads': 1,  # Aantal CPU threads (1-4)
        },
        'checkers': {
            'play_vs_computer': False,
            'strict_touch_move': False,  # Touch-move regel
            'cake_difficulty': 5,  # 1-10 (1=zwakst, 10=sterkst)
            'cake_think_time': 1000,  # Denktijd in ms (500-5000)
        }
    }
    
    # Map setting keys to their sections (voor backward compatibility)
    KEY_TO_SECTION = {
        # Hardware
        'brightness': 'hardware',
        'power_profile': 'hardware',
        # General
        'screensaver_audio': 'general',
        # Debug
        'show_coordinates': 'debug',
        'debug_sensors': 'debug',
        'validate_board_state': 'debug',
        # Chess
        'play_vs_computer': 'chess',
        'strict_touch_move': 'chess',
        'stockfish_skill_level': 'chess',
        'stockfish_think_time': 'chess',
        'stockfish_depth': 'chess',
        'stockfish_threads': 'chess',
        # Checkers
        'ai_difficulty': 'checkers',
        'ai_think_time': 'checkers',
    }
    
    @staticmethod
    def set_in_dict(settings_dict, key, value, section=None):
        """
        Helper om waarde te zetten in settings dict (voor temp_settings)
        
        Args:
            settings_dict: De settings dict (kan nested zijn met sections)
            key: Setting key
            value: Nieuwe waarde
            section: Optional sectie naam
        """
        if section:
            if section not in settings_dict:
                settings_dict[section] = {}
            settings_dict[section][key] = value
        else:
            # Gebruik KEY_TO_SECTION mapping
            target_section = Settings.KEY_TO_SECTION.get(key)
            if target_section:
                if target_section not in settings_dict:
                    settings_dict[target_section] = {}
                settings_dict[target_section][key] = value
            else:
                # Onbekende key: zet direct (voor backward compatibility met flat dicts)
                settings_dict[key] = value
    
    @staticmethod
    def get_from_dict(settings_dict, key, default=None, section=None):
        """
        Helper om waarde uit settings dict te halen (voor temp_settings)
        
        Args:
            settings_dict: De settings dict (kan nested zijn met sections)
            key: Setting key
            default: Default waarde
            section: Optional sectie naam
        
        Returns:
            Setting waarde
        """
        if section:
            return settings_dict.get(section, {}).get(key, default)
        else:
            # Zoek in alle secties
            for section_dict in settings_dict.values():
                if isinstance(section_dict, dict) and key in section_dict:
                    return section_dict[key]
            # Als niet gevonden, probeer direct (backward compatibility)
            return settings_dict.get(key, default)
    
    def __init__(self, settings_file='settings.json'):
        """
        Initialiseer settings
        
        Args:
            settings_file: Pad naar settings bestand
        """
        self.settings_file = settings_file
        self.settings = self._deep_copy_defaults()
        self.load()
    
    def _deep_copy_defaults(self):
        """Maak deep copy van DEFAULTS dict"""
        import copy
        return copy.deepcopy(self.DEFAULTS)
    
    def load(self):
        """Laad settings van disk, gebruik defaults als bestand niet bestaat"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Deep merge: update nested dicts
                    self._deep_update(self.settings, loaded_settings)
                print(f"Settings geladen van {self.settings_file}")
            except Exception as e:
                print(f"Fout bij laden settings: {e}")
                print("Gebruik default settings")
        else:
            print("Geen settings bestand gevonden, gebruik defaults")
            self.save()  # Maak settings.json met defaults
    
    def _deep_update(self, base_dict, update_dict):
        """Update nested dictionary recursively"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _clean_for_json(self, obj, seen=None):
        """
        Recursief opschonen van object voor JSON serialisatie
        
        Args:
            obj: Object om op te schonen
            seen: Set van al geziene objecten (voor circular reference detectie)
            
        Returns:
            JSON-serialiseerbaar object
        """
        if seen is None:
            seen = set()
        
        # Check voor circular reference
        obj_id = id(obj)
        if obj_id in seen:
            return None  # Skip circular references
        
        if isinstance(obj, dict):
            seen.add(obj_id)
            result = {}
            for key, value in obj.items():
                clean_value = self._clean_for_json(value, seen.copy())
                if clean_value is not None or isinstance(value, type(None)):
                    result[key] = clean_value
            return result
        elif isinstance(obj, (list, tuple)):
            seen.add(obj_id)
            return [self._clean_for_json(item, seen.copy()) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            # Niet-serialiseerbaar type
            return None
    
    def save(self):
        """Sla settings op naar disk"""
        try:
            # Maak een clean copy zonder circular references
            clean_settings = self._clean_for_json(self.settings)
            
            with open(self.settings_file, 'w') as f:
                json.dump(clean_settings, f, indent=2)
            print(f"Settings opgeslagen naar {self.settings_file}")
        except Exception as e:
            print(f"Fout bij opslaan settings: {e}")
            import traceback
            traceback.print_exc()
    
    def get(self, key, default=None, section=None):
        """
        Haal setting op (backwards compatible + nieuwe sectie support)
        
        Args:
            key: Setting key
            default: Default waarde als key niet bestaat
            section: Optional sectie naam (hardware, debug, chess, checkers)
        
        Returns:
            Setting waarde
        """
        if section:
            # Nieuwe manier: get('brightness', section='hardware')
            return self.settings.get(section, {}).get(key, default)
        else:
            # Backwards compatible: zoek in alle secties
            for section_dict in self.settings.values():
                if isinstance(section_dict, dict) and key in section_dict:
                    return section_dict[key]
            return default
    
    def set(self, key, value, section=None):
        """
        Zet setting waarde
        
        Args:
            key: Setting key
            value: Nieuwe waarde
            section: Optional sectie naam (hardware, debug, chess, checkers)
        """
        if section:
            # Nieuwe manier: set('brightness', 50, section='hardware')
            if section not in self.settings:
                self.settings[section] = {}
            self.settings[section][key] = value
        else:
            # Backwards compatible: gebruik KEY_TO_SECTION mapping
            target_section = self.KEY_TO_SECTION.get(key)
            if target_section:
                if target_section not in self.settings:
                    self.settings[target_section] = {}
                self.settings[target_section][key] = value
            else:
                # Onbekende key: probeer te vinden in bestaande secties
                for section_name, section_dict in self.settings.items():
                    if isinstance(section_dict, dict) and key in section_dict:
                        section_dict[key] = value
                        return
                # Als helemaal niet gevonden, zet in 'general' sectie
                if 'general' not in self.settings:
                    self.settings['general'] = {}
                self.settings['general'][key] = value
    
    def get_section(self, section):
        """
        Haal hele sectie op
        
        Args:
            section: Sectie naam (hardware, debug, chess, checkers)
        
        Returns:
            Dict met alle settings in sectie
        """
        return self.settings.get(section, {})
    
    def update_section(self, section, updates):
        """
        Update meerdere settings in een sectie
        
        Args:
            section: Sectie naam
            updates: Dict met key->value updates
        """
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section].update(updates)
    
    def toggle(self, key, section=None):
        """
        Toggle boolean setting
        
        Args:
            key: Setting key
            section: Optional sectie naam
        
        Returns:
            Nieuwe waarde
        """
        current_value = self.get(key, False, section=section)
        new_value = not current_value
        self.set(key, new_value, section=section)
        return new_value
    
    def get_max_brightness(self):
        """Get max brightness % allowed by current power profile"""
        power_limit = self.get('power_profile', 1.5, section='hardware')
        return self.POWER_PROFILES.get(power_limit, 60)
    
    def get_temp_copy(self):
        """
        Maak deep copy van huidige settings voor temp editing
        
        Returns:
            Deep copy van self.settings dict
        """
        import copy
        return copy.deepcopy(self.settings)
