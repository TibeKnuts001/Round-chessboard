#!/usr/bin/env python3
"""
Sensor to LED Mapping Test v2 - OLD/DEPRECATED

LEGACY TEST FILE - Gebruikt niet meer in productie!

WAARSCHUWING: Dit bestand heette 'chess.py' en veroorzaakte een naming conflict
met de python-chess library! Import van chess.Board() faalde hierdoor.

Real-time sensor→LED mapping: light LED waar een piece staat.
Gebruikt voor hardware integration testing.

Voor de echte applicatie zie: chessgame.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from lib.hardware.leds import LEDController
from lib.hardware.sensors import SensorReader
from lib.hardware.mapping import ChessMapper
from lib.debug import ChessDebug


class ChessBoard:
    """Combineert Hall sensoren en LEDs voor schaakbord"""
    
    # Configuratie
    BRIGHTNESS = 15  
    
    def __init__(self, brightness=BRIGHTNESS):
        """Initialiseer LEDs en Hall sensoren"""
        print("Initialiseer Chess Board...")
        self.leds = LEDController(brightness=brightness)
        self.sensors = SensorReader()
        print("Chess Board klaar!")
    
    def update_leds(self, color=(255, 255, 255, 0)):
        """
        Update LEDs op basis van hall sensor status
        
        Args:
            color: (red, green, blue, white) tuple voor actieve posities
        """
        # Lees alle hall sensoren
        sensor_values = self.sensors.read_all()
        
        # Zet alle LEDs uit
        self.leds.clear()
        
        # Zet LED aan waar hall sensor actief is (inverse: 0 = magneet aanwezig)
        for i in range(64):
            if not sensor_values[i]:  # LOW = magneet gedetecteerd
                r, g, b, w = color
                self.leds.set_led(i, r, g, b, w)
        
        # Update de LEDs
        self.leds.show()
    
    def print_status(self):
        """Print schaakbord met actieve posities"""
        sensor_values = self.sensors.read_all()
        
        # Print pure raw sensor data
        raw_low = [i for i, v in enumerate(sensor_values) if not v]  # Sensors die LOW zijn
        raw_high = [i for i, v in enumerate(sensor_values) if v]     # Sensors die HIGH zijn
        print(f"\nRAW Sensors LOW (0): {raw_low}")
        print(f"RAW Sensors HIGH (1): {raw_high}")
        
        # Inverse logica: LOW = magneet aanwezig
        active_values = [not v for v in sensor_values]
        
        # Print schaakbord
        ChessDebug.print_board(active_values)
        
        # Print actieve posities
        active_positions = ChessDebug.get_active_positions(active_values)
        print(f"Actieve posities ({len(active_positions)}): {', '.join(active_positions) if active_positions else 'Geen'}")
        print()
    
    def cleanup(self):
        """Cleanup: zet alles uit"""
        self.leds.cleanup()
        self.sensors.cleanup()


def main():
    """Hoofdprogramma"""
    print("=" * 50)
    print("Chess Board - Hall Sensor LED Mapping")
    print("=" * 50)
    print("4 kwarten x 16 LEDs = 64 LEDs")
    print("8 chips x 8 inputs = 64 hall sensoren")
    print("=" * 50)
    print("\nMapping:")
    print("  Chips 1-2 (hall 0-15)  → Kwart 1 (LED 0-15)")
    print("  Chips 3-4 (hall 16-31) → Kwart 2 (LED 16-31)")
    print("  Chips 5-6 (hall 32-47) → Kwart 3 (LED 32-47)")
    print("  Chips 7-8 (hall 48-63) → Kwart 4 (LED 48-63)")
    print("=" * 50)
    print("\nDruk op Ctrl+C om te stoppen\n")
    
    # Initialiseer schaakbord
    board = ChessBoard()
    
    try:
        while True:
            # Update LEDs op basis van hall sensoren
            # Wit licht voor actieve posities
            board.update_leds(color=(255, 255, 255, 0))
            
            # Print status
            board.print_status()
            
    except KeyboardInterrupt:
        print("\n\nProgramma gestopt")
    finally:
        board.cleanup()
        print("Schaakbord uitgezet")


if __name__ == '__main__':
    main()
