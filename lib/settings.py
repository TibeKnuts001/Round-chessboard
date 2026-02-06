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
    
    # Default settings
    DEFAULTS = {
        'show_coordinates': True,
        'brightness': 20,
        'debug_sensors': False,
        'play_vs_computer': False,
        'stockfish_skill_level': 10,  # 0-20 (0=zwakst, 20=sterkst)
        'stockfish_think_time': 1000,  # Denktijd in ms (500-5000)
        'stockfish_depth': 15,  # Maximale zoekdiepte (5-25)
        'stockfish_threads': 1,  # Aantal CPU threads (1-4)
        'strict_touch_move': False,  # Touch-move regel: mag niet terugzetten op originele positie
        'validate_board_state': True,  # Valideer fysiek bord vs engine state (pause bij mismatch)
        'power_profile': 1.5,  # Power limit in Ampere (0.5, 1.0, 1.5, 2.0, 2.5)
    }
    
    def __init__(self, settings_file='settings.json'):
        """
        Initialiseer settings
        
        Args:
            settings_file: Pad naar settings bestand
        """
        self.settings_file = settings_file
        self.settings = self.DEFAULTS.copy()
        self.load()
    
    def load(self):
        """Laad settings van disk, gebruik defaults als bestand niet bestaat"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Update settings met geladen waarden
                    self.settings.update(loaded_settings)
                print(f"Settings geladen van {self.settings_file}")
            except Exception as e:
                print(f"Fout bij laden settings: {e}")
                print("Gebruik default settings")
        else:
            print("Geen settings bestand gevonden, gebruik defaults")
            self.save()  # Maak settings.json met defaults
    
    def save(self):
        """Sla settings op naar disk"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            print(f"Settings opgeslagen naar {self.settings_file}")
        except Exception as e:
            print(f"Fout bij opslaan settings: {e}")
    
    def get(self, key, default=None):
        """Haal setting op"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Zet setting en sla op"""
        self.settings[key] = value
        self.save()
    
    def toggle(self, key):
        """Toggle boolean setting"""
        if key in self.settings and isinstance(self.settings[key], bool):
            self.settings[key] = not self.settings[key]
            self.save()
            return self.settings[key]
    
    def get_max_brightness(self):
        """Get max brightness % allowed by current power profile"""
        power_limit = self.settings.get('power_profile', 1.5)
        return self.POWER_PROFILES.get(power_limit, 60)
