#!/usr/bin/env python3
"""
Sound Manager - Game sound effects

Beheert sound effects voor game events:
- check.mp3: Speler staat schaak
- checkmate.mp3: Schaakmat (game over)
- mismatch.mp3: Ongeldige zet

Gebruikt pygame.mixer.Sound voor effects (niet music channel).
Dit zorgt ervoor dat effects niet de screensaver muziek onderbreken.
"""

import os
import pygame


class SoundManager:
    """Beheert game sound effects"""
    
    def __init__(self, settings):
        """
        Initialiseer sound manager
        
        Args:
            settings: Settings object voor audio configuratie
        """
        self.settings = settings
        self.sounds = {}
        self.initialized = False
        
        # Probeer pygame mixer te initialiseren
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.initialized = True
        except Exception as e:
            print(f"✗ Kon pygame.mixer niet initialiseren: {e}")
            self.initialized = False
            return
        
        # Laad sound effects
        self._load_sounds()
    
    def _load_sounds(self):
        """Laad alle sound effect bestanden"""
        sound_files = {
            'check': 'assets/audio/check.mp3',
            'checkmate': 'assets/audio/checkmate.mp3',
            'mismatch': 'assets/audio/mismatch.mp3',
            'capture': 'assets/audio/capture.mp3',
        }
        
        for name, path in sound_files.items():
            try:
                if os.path.exists(path):
                    self.sounds[name] = pygame.mixer.Sound(path)
                    print(f"✓ Geladen: {name}.mp3")
                else:
                    print(f"✗ Niet gevonden: {path}")
            except Exception as e:
                print(f"✗ Kon {name} niet laden: {e}")
    
    def _is_enabled(self):
        """Check of sound effects enabled zijn in settings"""
        if not self.initialized:
            return False
        
        return self.settings.get('sound_effects', True, section='general')
    
    def play_check(self):
        """Speel check sound effect (schaak)"""
        if not self._is_enabled():
            return
        
        if 'check' in self.sounds:
            try:
                self.sounds['check'].play()
            except Exception as e:
                print(f"✗ Kon check sound niet afspelen: {e}")
    
    def play_checkmate(self):
        """Speel checkmate sound effect (schaakmat)"""
        if not self._is_enabled():
            return
        
        if 'checkmate' in self.sounds:
            try:
                self.sounds['checkmate'].play()
            except Exception as e:
                print(f"✗ Kon checkmate sound niet afspelen: {e}")
    
    def play_mismatch(self):
        """Speel mismatch sound effect (ongeldige zet)"""
        if not self._is_enabled():
            return
        
        if 'mismatch' in self.sounds:
            try:
                self.sounds['mismatch'].play()
            except Exception as e:
                print(f"✗ Kon mismatch sound niet afspelen: {e}")
    
    def play_capture(self):
        """Speel capture sound effect (stuk slaan)"""
        if not self._is_enabled():
            return
        
        if 'capture' in self.sounds:
            try:
                self.sounds['capture'].play()
            except Exception as e:
                print(f"✗ Kon capture sound niet afspelen: {e}")
    
    def set_volume(self, volume):
        """
        Zet volume voor alle sound effects
        
        Args:
            volume: Volume 0.0 (stil) tot 1.0 (max)
        """
        for sound in self.sounds.values():
            sound.set_volume(volume)
