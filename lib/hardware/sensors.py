#!/usr/bin/env python3
"""
Hall Sensor Library voor Chess Board

Leest 64 Hall-effect sensors om te detecteren of er stukken op velden staan.
Magneten in de stukken triggeren de sensors voor piece detection.

Hardware:
- 64x Hall sensors (één per veld)
- 8x 74HC165 8-bit parallel-in serial-out shift registers
- GPIO pins: Data (pin 11), Clock (pin 13), Latch (pin 15)

Functionaliteit:
- Realtime board state reading (welke velden bezet)
- Debouncing voor stabiele readings
- Change detection (verschil tussen oude en nieuwe state)
- Batch read van alle 64 sensors in één cyclus

Working principle:
- Latch puls → parallel load alle 64 sensor states
- 64 clock pulses → serial shift alle bits uit via data pin
- Result: 64-bit array met 1 = piece detected, 0 = empty

Hoofdklasse:
- SensorReader: Low-level GPIO interface naar shift registers

Wordt gebruikt door: chessgame.py (voor physical piece detection)
"""

import time
import RPi.GPIO as GPIO


class SensorReader:
    """Leest Hall sensoren via 74HC165 shift registers"""
    
    # Pin configuratie (BCM numbering)
    DATA_PIN = 9    # GPIO9 (pin 21) - MISO / Q7
    CLOCK_PIN = 11  # GPIO11 (pin 23) - SCLK / CLK  
    LATCH_PIN = 25  # GPIO25 (pin 22) - /PL (latch/load)
    NUM_CHIPS = 8
    
    def __init__(self, data_pin=DATA_PIN, clock_pin=CLOCK_PIN, latch_pin=LATCH_PIN, num_chips=NUM_CHIPS):
        """
        Initialiseer shift register keten
        
        Args:
            data_pin: GPIO pin voor data (MISO)
            clock_pin: GPIO pin voor clock (SCLK)
            latch_pin: GPIO pin voor latch (/PL)
            num_chips: Aantal cascaded 74HC165 chips
        """
        self.data_pin = data_pin
        self.clock_pin = clock_pin
        self.latch_pin = latch_pin
        self.num_chips = num_chips
        self.num_inputs = num_chips * 8
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup pins (data pin met pull-down voor stabiele readings)
        GPIO.setup(self.data_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.clock_pin, GPIO.OUT)
        GPIO.setup(self.latch_pin, GPIO.OUT)
        
        # Initiële staat
        GPIO.output(self.clock_pin, GPIO.LOW)
        GPIO.output(self.latch_pin, GPIO.HIGH)
    
    def read_all(self):
        """
        Lees alle inputs uit de cascaded shift registers
        
        Returns:
            List van 64 boolean waarden (True = high/magneet gedetecteerd)
        """
        # Latch de huidige inputs (laad parallel data)
        GPIO.output(self.latch_pin, GPIO.LOW)
        time.sleep(0.000001)  # 1 microseconde delay voor stable latch
        GPIO.output(self.latch_pin, GPIO.HIGH)
        time.sleep(0.000001)  # 1 microseconde delay na latch
        
        # Lees alle bits uit via shift
        values = []
        for i in range(self.num_inputs):
            # Lees huidige bit
            bit = GPIO.input(self.data_pin)
            values.append(bool(bit))
            
            # Clock puls voor volgende bit (met kleine delays voor stable timing)
            GPIO.output(self.clock_pin, GPIO.HIGH)
            time.sleep(0.000001)  # 1 microseconde clock high time
            GPIO.output(self.clock_pin, GPIO.LOW)
            time.sleep(0.000001)  # 1 microseconde clock low time
        
        # Keer de volgorde om - cascaded shift registers geven data achterstevoren
        values.reverse()
        
        return values
    
    def cleanup(self):
        """Cleanup GPIO"""
        GPIO.cleanup([self.data_pin, self.clock_pin, self.latch_pin])
