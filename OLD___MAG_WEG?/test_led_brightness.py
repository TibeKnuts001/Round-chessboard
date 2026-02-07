#!/usr/bin/env python3
"""
LED Brightness Test - OLD/DEPRECATED

LEGACY TEST FILE - Gebruikt niet meer in productie!

Test alle 64 LEDs op maximale helderheid (100%).
Gebruikt voor hardware validation tijdens development.

Functionaliteit:
- Zet alle LEDs op wit licht (RGB 255,255,255)
- Test brightness control op 100%
- Blijft aan tot Ctrl+C

Voor de echte applicatie zie: chessgame.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from lib.hardware.leds import LEDController


def main():
    """Test alle LEDs op maximale helderheid"""
    print("=" * 50)
    print("Test Alle LEDs op 100%")
    print("=" * 50)
    print("Zet alle 64 LEDs op wit licht (100% brightness)")
    print("=" * 50)
    print("\nDruk op Ctrl+C om te stoppen\n")
    
    # Initialiseer LEDs met 100% brightness
    leds = LEDController(brightness=255)
    
    try:
        print("Alle LEDs AAN (wit licht, 100%)...")
        
        # Zet alle LEDs op wit
        for i in range(64):
            leds.set_led(i, 255, 255, 255, 0)  # RGB wit
        
        leds.show()
        
        # Blijf aan tot Ctrl+C
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nTest gestopt")
    finally:
        leds.cleanup()
        print("Alle LEDs uitgezet")


if __name__ == '__main__':
    main()
