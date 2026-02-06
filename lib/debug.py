#!/usr/bin/env python3
"""
Chess Debug Utilities

Helper functies voor development en troubleshooting.
Visualiseert hardware sensor states en board mappings.

Functionaliteit:
- Sensor state pretty printing (8x8 grid in terminal)
- Sensor-to-position mapping validatie
- Occupied squares detection en formatting
- Terminal output voor debugging zonder GUI

Debug output formaten:
1. Sensor grid (64 bits als 8x8 matrix)
   - 1 = sensor triggered (piece detected)
   - 0 = no signal (empty square)
   - Output: visuele 8x8 grid in console

2. Position lists
   - Bezette velden in chess notatie: ["e2", "e4", ...]
   - Handig voor state comparison

Use cases:
- Sensor calibratie tijdens hardware setup
- Board state verification tijdens development
- Debugging piece detection issues
- Validatie van sensor→position mapping

Hoofdklasse:
- ChessDebug: Static utility methods voor debug output

Wordt gebruikt door: Development/testing (niet in productie)
"""

from lib.hardware.mapping import ChessMapper


class ChessDebug:
    """Debug en visualisatie functies"""
    
    # Kolom letters
    COLUMNS = 'ABCDEFGH'
    
    @classmethod
    def chess_to_coordinates(cls, chess_notation):
        """
        Converteer schaaknotatie naar (rij, kolom) coördinaten
        
        Args:
            chess_notation: String zoals 'A1', 'E4', etc.
            
        Returns:
            Tuple (rij, kolom) waarbij rij 0-7 = rij 1-8, kolom 0-7 = A-H
            of None als ongeldig
        """
        if len(chess_notation) != 2:
            return None
        
        col_letter = chess_notation[0].upper()
        row_num = chess_notation[1]
        
        if col_letter not in cls.COLUMNS or not row_num.isdigit():
            return None
        
        col = cls.COLUMNS.index(col_letter)
        row = int(row_num) - 1
        
        return (row, col)
    
    @classmethod
    def print_board(cls, sensor_values):
        """
        Print schaakbord met sensor status
        
        Args:
            sensor_values: List van 64 booleans (True = actief)
        """
        # Maak 8x8 grid
        grid = [[False] * 8 for _ in range(8)]
        
        # Vul grid met sensor waarden en verzamel actieve sensors
        active_sensors = []
        for sensor_num, is_active in enumerate(sensor_values):
            chess_pos = ChessMapper.sensor_to_chess(sensor_num)
            if chess_pos:
                coords = cls.chess_to_coordinates(chess_pos)
                if coords:
                    row, col = coords
                    grid[row][col] = is_active
                    if is_active:
                        active_sensors.append(sensor_num)
        
        # Print board met status
        print("\n  A B C D E F G H")
        print("  ---------------")
        for row in range(7, -1, -1):  # Van rij 7 (=8) naar rij 0 (=1)
            print(f"{row + 1}|", end="")
            for col in range(8):
                symbol = "■" if grid[row][col] else "□"
                print(symbol, end=" ")
            print(f"|{row + 1}")
        print("  ---------------")
        print("  A B C D E F G H\n")
        
        # Print actieve sensor nummers
        if active_sensors:
            print(f"Actieve sensors: {', '.join(map(str, active_sensors))}")
        else:
            print("Actieve sensors: Geen")
    
    @classmethod
    def get_active_positions(cls, sensor_values):
        """
        Geef lijst van actieve posities in schaaknotatie
        
        Args:
            sensor_values: List van 64 booleans
            
        Returns:
            List van strings zoals ['A1', 'E4', ...]
        """
        active = []
        for sensor_num, is_active in enumerate(sensor_values):
            if is_active:
                pos = ChessMapper.sensor_to_chess(sensor_num)
                if pos:
                    active.append(pos)
        return active
