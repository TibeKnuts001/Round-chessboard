#!/usr/bin/env python3
"""
Hall Sensor Monitor - OLD/DEPRECATED

LEGACY TEST FILE - Gebruikt niet meer in productie!

Monitort Hall sensors en print state changes in terminal.
Gebruikt voor sensor calibratie en debugging.

Functionaliteit:
- Leest continue alle 64 Hall sensors
- Print alleen veranderingen (piece geplaatst/verwijderd)
- Toont chess positie (A1-H8) bij elke change
- Geen LED feedback, pure sensor monitoring

Voor de echte applicatie zie: chessgame.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from lib.hardware.sensors import SensorReader
from lib.hardware.mapping import ChessMapper


def main():
    print("=" * 60)
    print("HALL SENSOR TEST")
    print("=" * 60)
    print("Drukt state veranderingen af")
    print("Druk Ctrl+C om te stoppen\n")
    
    # Initialiseer sensors
    sensors = SensorReader()
    
    # Initiële state
    previous_state = {}
    
    # Lees eerste state
    sensor_values = sensors.read_all()
    for i in range(64):
        chess_pos = ChessMapper.sensor_to_chess(i)
        if chess_pos:
            # True = stuk staat op veld (sensor LOW - inverse logic)
            previous_state[chess_pos] = not sensor_values[i]
    
    print("Initiële state gelezen. Monitor gestart...\n")
    
    try:
        while True:
            # Lees huidige state
            sensor_values = sensors.read_all()
            current_state = {}
            
            for i in range(64):
                chess_pos = ChessMapper.sensor_to_chess(i)
                if chess_pos:
                    current_state[chess_pos] = not sensor_values[i]
            
            # Detecteer veranderingen
            current_positions = set(pos for pos, active in current_state.items() if active)
            previous_positions = set(pos for pos, active in previous_state.items() if active)
            
            added = current_positions - previous_positions
            removed = previous_positions - current_positions
            
            # Print veranderingen
            if removed:
                for pos in sorted(removed):
                    print(f"[-] Sensor {pos}: GEEN stuk meer (sensor HIGH)")
            
            if added:
                for pos in sorted(added):
                    print(f"[+] Sensor {pos}: STUK gedetecteerd (sensor LOW)")
            
            # Update previous state
            previous_state = current_state.copy()
            
            # Korte pauze (10ms)
            time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n\nTest gestopt")
    finally:
        sensors.cleanup()
        print("Sensors cleanup done")


if __name__ == '__main__':
    main()
