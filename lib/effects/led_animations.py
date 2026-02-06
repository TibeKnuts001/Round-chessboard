#!/usr/bin/env python3
"""
LED Animation Effects Library

Library voor LED animatie effecten tijdens idle state (spel niet gestart).
Bevat verschillende visuele effecten die op de achtergrond draaien.

Effecten:
- rainbow_wave: Regenboog golf over bord
- breathing: Fade in/out ademhaling effect
- color_fade: Smooth color transitions
- circular_wave: Circulaire golf patronen
- sparkle: Random twinkelende LEDs

Usage:
    animator = LEDAnimator(led_controller)
    animator.start_random_animation()
    # Later...
    animator.stop()
"""

import time
import math
import random
import threading


def hsv_to_rgb(h, s, v):
    """
    Converteer HSV naar RGB
    
    Args:
        h: Hue (0-360)
        s: Saturation (0-1)
        v: Value/brightness (0-1)
    
    Returns:
        (r, g, b) tuple (0-255)
    """
    h = h / 60.0
    i = int(h)
    f = h - i
    
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))
    
    i = i % 6
    
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q
    
    return int(r * 255), int(g * 255), int(b * 255)


class LEDAnimator:
    """Manager voor LED animatie effecten"""
    
    def __init__(self, led_controller):
        """
        Initialiseer animator
        
        Args:
            led_controller: LEDController instance
        """
        self.leds = led_controller
        self.running = False
        self.thread = None
        self.current_effect = None
        self.start_time = 0
        
        # Beschikbare effecten met parameters
        self.effects = {
            'rainbow_wave': {
                'func': self._rainbow_wave,
                'speed': 0.05,
                'duration': 15
            },
            'breathing': {
                'func': self._breathing,
                'speed': 0.02,
                'duration': 12,
                'color': (255, 0, 100)
            },
            'color_fade': {
                'func': self._color_fade,
                'speed': 0.05,
                'duration': 12
            },
            'circular_wave': {
                'func': self._circular_wave,
                'speed': 0.03,
                'duration': 15
            },
            'sparkle': {
                'func': self._sparkle,
                'speed': 0.1,
                'duration': 10,
                'color': (100, 150, 255)
            }
        }
    
    def start_random_animation(self):
        """Start een willekeurige animatie in background thread"""
        if self.running:
            return
        
        # Kies random effect
        self.current_effect = random.choice(list(self.effects.keys()))
        print(f"Starting LED animation: {self.current_effect}")
        
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.thread.start()
    
    def start_animation(self, effect_name):
        """
        Start specifieke animatie
        
        Args:
            effect_name: Naam van effect uit self.effects
        """
        if effect_name not in self.effects:
            print(f"Unknown effect: {effect_name}")
            return
        
        if self.running:
            self.stop()
        
        self.current_effect = effect_name
        print(f"Starting LED animation: {effect_name}")
        
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop huidige animatie"""
        if not self.running:
            return
        
        print("Stopping LED animation")
        self.running = False
        
        # Wacht tot thread klaar is (max 1 sec)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        
        # Clear LEDs
        self.leds.clear()
        self.leds.show()
    
    def _animation_loop(self):
        """Main animatie loop (draait in background thread)"""
        effect_config = self.effects[self.current_effect]
        duration = effect_config.get('duration', 10)
        
        while self.running and (time.time() - self.start_time) < duration:
            try:
                effect_config['func'](effect_config)
            except Exception as e:
                print(f"Animation error: {e}")
                break
        
        # Als duration bereikt en nog running, start nieuwe random animatie
        if self.running:
            self.running = False
            self.start_random_animation()
    
    def _rainbow_wave(self, config):
        """Regenboog golf over alle LEDs"""
        for i in range(64):
            # Bereken hue op basis van LED positie en tijd
            hue = (i * 360 / 64 + time.time() * 100) % 360
            r, g, b = hsv_to_rgb(hue, 1.0, 0.8)  # Brightness 0.8 voor minder fel
            self.leds.set_led(i, r, g, b, 0)
        
        self.leds.show()
        time.sleep(config['speed'])
    
    def _breathing(self, config):
        """Ademhaling effect - fade in/out"""
        # Bereken brightness met sinus (smooth fade)
        brightness = (math.sin(time.time() * 2) + 1) / 2  # 0-1
        brightness = brightness * 0.6  # Max brightness 0.6
        
        color = config.get('color', (255, 0, 100))
        r = int(color[0] * brightness)
        g = int(color[1] * brightness)
        b = int(color[2] * brightness)
        
        for i in range(64):
            self.leds.set_led(i, r, g, b, 0)
        
        self.leds.show()
        time.sleep(config['speed'])
    
    def _color_fade(self, config):
        """Fade door verschillende kleuren"""
        hue = (time.time() * 50) % 360
        r, g, b = hsv_to_rgb(hue, 1.0, 0.7)  # Brightness 0.7
        
        for i in range(64):
            self.leds.set_led(i, r, g, b, 0)
        
        self.leds.show()
        time.sleep(config['speed'])
    
    def _circular_wave(self, config):
        """Golf effect in cirkel patroon"""
        offset = time.time() * 5
        
        for i in range(64):
            # Bereken positie in cirkel
            kwart = i // 16
            pos_in_kwart = i % 16
            
            # Totale positie in cirkel (0-63)
            circle_pos = kwart * 16 + pos_in_kwart
            
            # Bereken hue op basis van positie in cirkel
            hue = ((circle_pos * 360 / 64) + offset * 10) % 360
            brightness = (math.sin(circle_pos / 10.0 + offset) + 1) / 2
            brightness = brightness * 0.7  # Max brightness 0.7
            
            r, g, b = hsv_to_rgb(hue, 1.0, brightness)
            self.leds.set_led(i, r, g, b, 0)
        
        self.leds.show()
        time.sleep(config['speed'])
    
    def _sparkle(self, config):
        """Sparkle effect - willekeurige LEDs flikkeren"""
        self.leds.clear()
        
        color = config.get('color', (255, 255, 255))
        
        # Willekeurige LEDs aan
        num_sparkles = random.randint(5, 15)
        for _ in range(num_sparkles):
            led = random.randint(0, 63)
            brightness = random.uniform(0.3, 0.8)  # Max 0.8
            r = int(color[0] * brightness)
            g = int(color[1] * brightness)
            b = int(color[2] * brightness)
            self.leds.set_led(led, r, g, b, 0)
        
        self.leds.show()
        time.sleep(config['speed'])
