#!/usr/bin/env python3
"""
Chess Mapping

Vertaallaag tussen hardware en schaaknotatie.
Mapt sensor/LED nummers (0-63) naar schaakbord posities (A1-H8) en omgekeerd.

Functionaliteit:
- Sensor nummer → schaakpositie (bijv. 0 → "a1", 63 → "h8")
- Schaakpositie → LED nummer voor indicator lights
- Batch conversies voor meerdere posities tegelijk
- Support voor beide oriëntaties (wit onder/zwart onder)

Hardware layout:
- 64 Hall sensors (74HC165 shift registers) detecteren stukken
- 64 RGBW LEDs (SK5812) onder elk veld voor move hints
- Fysieke layout: rij 0-7 van links naar rechts, kolom 0-7 van beneden naar boven

Hoofdklasse:
- ChessMapper: Statische methods voor bi-directionele mapping

Wordt gebruikt door: sensors.py, leds.py, debug.py
"""


class ChessMapper:
    """Mapt hardware nummers naar schaakbord posities"""
    
    # Mapping tabel: sensor nummer -> schaaknotatie
    # Geroteerd 90° MET DE KLOK MEE voor printplaat aansluiting
    # Origineel: sensor 12 = A1, nu na rotatie: sensor 12 = A8
    SENSOR_TO_CHESS = {
        # Rij 1 → Kolom A (van boven naar onder: A8-A1)
        12: "A8",
        13: "A7",
        14: "A6",
        15: "A5",
        16: "A4",
        20: "A3",
        24: "A2",
        28: "A1",
        # Rij 2 → Kolom B
        8: "B8",
        9: "B7",
        10: "B6",
        11: "B5",
        17: "B4",
        21: "B3",
        25: "B2",
        29: "B1",
        # Rij 3 → Kolom C
        4: "C8",
        5: "C7",
        6: "C6",
        7: "C5",
        18: "C4",
        22: "C3",
        26: "C2",
        30: "C1",
        # Rij 4 → Kolom D
        0: "D8",
        1: "D7",
        2: "D6",
        3: "D5",
        19: "D4",
        23: "D3",
        27: "D2",
        31: "D1",
        # Rij 5 → Kolom E (omgekeerde volgorde in origineel)
        32: "E1",
        33: "E2",
        34: "E3",
        35: "E4",
        51: "E5",
        55: "E6",
        59: "E7",
        63: "E8",
        # Rij 6 → Kolom F
        36: "F1",
        37: "F2",
        38: "F3",
        39: "F4",
        50: "F5",
        54: "F6",
        58: "F7",
        62: "F8",
        # Rij 7 → Kolom G
        40: "G1",
        41: "G2",
        42: "G3",
        43: "G4",
        49: "G5",
        53: "G6",
        57: "G7",
        61: "G8",
        # Rij 8 → Kolom H
        44: "H1",
        45: "H2",
        46: "H3",
        47: "H4",
        48: "H5",
        52: "H6",
        56: "H7",
        60: "H8",
    }
    
    # Reverse mapping: schaaknotatie -> sensor nummer
    CHESS_TO_SENSOR = {v: k for k, v in SENSOR_TO_CHESS.items()}
    
    @classmethod
    def sensor_to_chess(cls, sensor_num):
        """
        Converteer sensor nummer naar schaaknotatie
        
        Args:
            sensor_num: Sensor nummer (0-63)
            
        Returns:
            String zoals 'A1', 'E4', etc. of None als ongeldig
        """
        return cls.SENSOR_TO_CHESS.get(sensor_num)
    
    @classmethod
    def chess_to_sensor(cls, chess_notation):
        """
        Converteer schaaknotatie naar sensor nummer
        
        Args:
            chess_notation: String zoals 'A1', 'E4', etc.
            
        Returns:
            Sensor nummer (0-63) of None als ongeldig
        """
        return cls.CHESS_TO_SENSOR.get(chess_notation.upper())
