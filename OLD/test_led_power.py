#!/usr/bin/env python3
"""
LED Power Measurement Test Script

Test tool om stroomverbruik van LEDs te meten bij verschillende helderheden.
Zet alle 64 LEDs op een constante helderheid zodat je met een multimeter
het stroomverbruik kunt meten.

Gebruik:
1. Voer percentage in (0-100)
2. Alle LEDs gaan op die helderheid (wit licht)
3. Meet stroomverbruik met multimeter
4. Voer nieuwe waarde in of 'q' om te stoppen

Voor power profiel calibratie: meet 0%, 10%, 20%, ..., 100%
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rpi_ws281x import PixelStrip


def set_all_leds(strip, percentage):
    """
    Zet alle 64 LEDs op een specifiek percentage helderheid
    
    Args:
        strip: PixelStrip instance
        percentage: Helderheid percentage (0-100)
    """
    # Bereken brightness waarde
    brightness_value = int((percentage / 100) * 255)
    strip.setBrightness(brightness_value)
    
    # Zet alle 64 LEDs op maximale waarde (wit licht = WRGB)
    for i in range(64):
        color = (255 << 24) | (255 << 16) | (255 << 8) | 255  # W, R, G, B allemaal max
        strip.setPixelColor(i, color)
    
    # Update de LEDs
    strip.show()


def main():
    print("=" * 60)
    print("LED POWER MEASUREMENT TEST")
    print("=" * 60)
    print()
    print("Dit script zet alle 64 LEDs op een constante helderheid.")
    print("Meet het stroomverbruik met een multimeter.")
    print()
    print("Commando's:")
    print("  0-100  : Zet LEDs op dit percentage helderheid")
    print("  q      : Quit")
    print()
    print("=" * 60)
    print()
    
    # Initialiseer LED strip rechtstreeks
    GPIO_PIN = 12
    LED_COUNT = 64
    strip = PixelStrip(LED_COUNT, GPIO_PIN)
    strip.begin()
    
    try:
        while True:
            # Vraag input
            user_input = input("Voer percentage in (0-100) of 'q' om te stoppen: ").strip()
            
            # Check voor quit
            if user_input.lower() in ['q', 'quit', 'exit']:
                print("\nStopping...")
                break
            
            # Probeer te parsen als integer
            try:
                percentage = int(user_input)
                
                # Valideer bereik
                if percentage < 0 or percentage > 100:
                    print("❌ Fout: Percentage moet tussen 0 en 100 zijn!")
                    continue
                
                # Zet LEDs
                set_all_leds(strip, percentage)
                
                # Bevestiging
                print(f"✓ Alle LEDs gezet op {percentage}% helderheid")
                print(f"  → Meet nu het stroomverbruik met multimeter")
                print()
                
            except ValueError:
                print("❌ Fout: Voer een geldig getal in (0-100)")
                continue
    
    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt - stopping...")
    
    finally:
        # Cleanup: zet alles uit
        print("\nCleaning up...")
        for i in range(64):
            strip.setPixelColor(i, 0)
        strip.show()
        print("Alle LEDs uitgezet. Klaar!")


if __name__ == '__main__':
    main()
