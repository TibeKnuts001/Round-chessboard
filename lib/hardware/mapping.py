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
    # Direct mapping van sensor naar chess positie (A1-H8)
    SENSOR_TO_CHESS = {
        # Rij 1
        12: "A1",
        13: "B1",
        14: "C1",
        15: "D1",
        16: "E1",
        20: "F1",
        24: "G1",
        28: "H1",
        # Rij 2
        8: "A2",
        9: "B2",
        10: "C2",
        11: "D2",
        17: "E2",
        21: "F2",
        25: "G2",
        29: "H2",
        # Rij 3
        4: "A3",
        5: "B3",
        6: "C3",
        7: "D3",
        18: "E3",
        22: "F3",
        26: "G3",
        30: "H3",
        # Rij 4
        0: "A4",
        1: "B4",
        2: "C4",
        3: "D4",
        19: "E4",
        23: "F4",
        27: "G4",
        31: "H4",
        # Rij 5 (omgekeerd t.o.v. rij 1-4)
        32: "H5",
        33: "G5",
        34: "F5",
        35: "E5",
        51: "D5",
        55: "C5",
        59: "B5",
        63: "A5",
        # Rij 6 (omgekeerd t.o.v. rij 1-4)
        36: "H6",
        37: "G6",
        38: "F6",
        39: "E6",
        50: "D6",
        54: "C6",
        58: "B6",
        62: "A6",
        # Rij 7 (omgekeerd t.o.v. rij 1-4)
        40: "H7",
        41: "G7",
        42: "F7",
        43: "E7",
        49: "D7",
        53: "C7",
        57: "B7",
        61: "A7",
        # Rij 8 (omgekeerd t.o.v. rij 1-4)
        44: "H8",
        45: "G8",
        46: "F8",
        47: "E8",
        48: "D8",
        52: "C8",
        56: "B8",
        60: "A8",
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
