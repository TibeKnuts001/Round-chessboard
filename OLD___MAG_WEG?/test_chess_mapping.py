#!/usr/bin/env python3
"""
Chess Board Mapping Test - OLD/DEPRECATED

LEGACY TEST FILE - Gebruikt niet meer in productie!

Test de mapping tussen chess posities (A1-H8) en LED nummers.
Licht elke rij (1-8) achter elkaar op om mapping te valideren.

Functionaliteit:
- Loop door rijen 1-8
- Light alle velden in de rij op (A-H)
- 2 seconden per rij
- Test chess_to_sensor mapping

Voor de echte applicatie zie: chessgame.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from lib.hardware.leds import LEDController
from lib.hardware.mapping import ChessMapper


def main():
    """Test elke rij van het schaakbord"""
    print("=" * 50)
    print("Chess Board Mapping Test")
    print("=" * 50)
    print("Test elke rij (1-8) van A tot H")
    print("2 seconden per rij")
    print("=" * 50)
    print("\nDruk op Ctrl+C om te stoppen\n")
    
    # Initialiseer LEDs
    leds = LEDController(brightness=15)  # Lage brightness voor test
    
    try:
        while True:
            # Test elke rij van 1 tot 8
            for rij in range(1, 9):
                print(f"\nRij {rij} - {chr(65)}1-H{rij}")
                
                # Zet alle LEDs uit
                leds.clear()
                
                # Licht alle posities in deze rij op
                for kolom in 'ABCDEFGH':
                    chess_pos = f"{kolom}{rij}"
                    sensor_num = ChessMapper.chess_to_sensor(chess_pos)
                    
                    if sensor_num is not None:
                        # Wit licht
                        leds.set_led(sensor_num, 255, 255, 255, 0)
                        print(f"  {chess_pos} -> sensor {sensor_num}")
                    else:
                        print(f"  {chess_pos} -> NIET GEMAPPED!")
                
                # Update LEDs
                leds.show()
                
                # Wacht 2 seconden
                time.sleep(2)
            
            print("\n" + "=" * 50)
            print("Herhaal test...")
            print("=" * 50)
            
    except KeyboardInterrupt:
        print("\n\nTest gestopt")
    finally:
        leds.cleanup()
        print("LEDs uitgezet")


if __name__ == '__main__':
    main()
