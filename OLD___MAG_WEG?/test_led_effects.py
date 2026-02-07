#!/usr/bin/env python3
"""
LED Effects Demo - OLD/DEPRECATED

LEGACY TEST FILE - Gebruikt niet meer in productie!

Demo van verschillende LED effecten: rainbow fade, pulsing, etc.
Gebruikt voor LED testing en visual validation tijdens development.

Functionaliteit:
- Rainbow cycle effect (HSV color wheel)
- Smooth color transitions
- Pulsing brightness effects
- Test van alle 64 LEDs tegelijk

Voor de echte applicatie zie: chessgame.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import math
from lib.hardware.leds import LEDController


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


def rainbow_wave(leds, duration=10, speed=0.05):
    """Regenboog golf over alle LEDs"""
    print("Effect: Rainbow Wave")
    start_time = time.time()
    
    while time.time() - start_time < duration:
        for i in range(64):
            # Bereken hue op basis van LED positie en tijd
            hue = (i * 360 / 64 + time.time() * 100) % 360
            r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
            leds.set_led(i, r, g, b, 0)
        
        leds.show()
        time.sleep(speed)


def breathing(leds, duration=10, speed=0.02, color=(255, 0, 100)):
    """Ademhaling effect - fade in/out"""
    print("Effect: Breathing")
    start_time = time.time()
    
    while time.time() - start_time < duration:
        # Bereken brightness met sinus (smooth fade)
        brightness = (math.sin(time.time() * 2) + 1) / 2  # 0-1
        
        r = int(color[0] * brightness)
        g = int(color[1] * brightness)
        b = int(color[2] * brightness)
        
        for i in range(64):
            leds.set_led(i, r, g, b, 0)
        
        leds.show()
        time.sleep(speed)


def color_fade(leds, duration=10, speed=0.05):
    """Fade door verschillende kleuren"""
    print("Effect: Color Fade")
    start_time = time.time()
    
    while time.time() - start_time < duration:
        hue = (time.time() * 50) % 360
        r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
        
        for i in range(64):
            leds.set_led(i, r, g, b, 0)
        
        leds.show()
        time.sleep(speed)


def circular_wave(leds, duration=10, speed=0.03):
    """Golf effect in cirkel patroon"""
    print("Effect: Circular Wave")
    start_time = time.time()
    
    # Posities in cirkel (0-15 per kwart, 4 kwarten)
    while time.time() - start_time < duration:
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
            
            r, g, b = hsv_to_rgb(hue, 1.0, brightness)
            leds.set_led(i, r, g, b, 0)
        
        leds.show()
        time.sleep(speed)


def sparkle(leds, duration=10, speed=0.1, color=(255, 255, 255)):
    """Sparkle effect - willekeurige LEDs flikkeren"""
    print("Effect: Sparkle")
    import random
    start_time = time.time()
    
    while time.time() - start_time < duration:
        leds.clear()
        
        # Willekeurige LEDs aan
        num_sparkles = random.randint(5, 15)
        for _ in range(num_sparkles):
            led = random.randint(0, 63)
            brightness = random.uniform(0.3, 1.0)
            r = int(color[0] * brightness)
            g = int(color[1] * brightness)
            b = int(color[2] * brightness)
            leds.set_led(led, r, g, b, 0)
        
        leds.show()
        time.sleep(speed)


def main():
    """Run alle effecten achter elkaar"""
    print("=" * 50)
    print("LED Effects - Fade Animaties")
    print("=" * 50)
    print("Druk op Ctrl+C om te stoppen\n")
    
    # Initialiseer LEDs met lage brightness
    leds = LEDController(brightness=20)
    
    try:
        while True:
            rainbow_wave(leds, duration=10)
            breathing(leds, duration=8, color=(255, 0, 100))
            color_fade(leds, duration=8)
            circular_wave(leds, duration=10)
            sparkle(leds, duration=8)
            print("\n" + "=" * 50)
            print("Herhaal effecten...")
            print("=" * 50 + "\n")
            
    except KeyboardInterrupt:
        print("\n\nEffecten gestopt")
    finally:
        leds.cleanup()
        print("LEDs uitgezet")


if __name__ == '__main__':
    main()
