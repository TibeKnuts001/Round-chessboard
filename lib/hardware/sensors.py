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
  Automatisch detecteert Raspberry Pi 5 en gebruikt de juiste backend

Wordt gebruikt door: chessgame.py (voor physical piece detection)
"""

import time


def is_raspberry_pi_5():
    """Detecteer of we op een Raspberry Pi 5 draaien"""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            is_pi5 = 'Raspberry Pi 5' in cpuinfo
            
            # Extract model info for debug
            for line in cpuinfo.split('\n'):
                if line.startswith('Model'):
                    model_info = line.split(':', 1)[1].strip()
                    print(f"[SENSOR DEBUG] Gedetecteerd bord: {model_info}")
                    break
            
            if is_pi5:
                print("[SENSOR DEBUG] → Raspberry Pi 5 gedetecteerd, gebruik lgpio")
            else:
                print("[SENSOR DEBUG] → Oudere Raspberry Pi gedetecteerd, gebruik RPi.GPIO")
            
            return is_pi5
    except Exception as e:
        print(f"[SENSOR DEBUG] Fout bij detectie: {e}, veronderstel oudere Pi")
        return False


# Import de juiste GPIO bibliotheek afhankelijk van de Pi versie
IS_PI5 = is_raspberry_pi_5()

if IS_PI5:
    # Pi 5 gebruikt lgpio
    import lgpio
else:
    # Oudere Pi's gebruiken RPi.GPIO
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
        self.is_pi5 = IS_PI5
        
        print(f"[SENSOR DEBUG] Initialiseer SensorReader met {self.num_inputs} inputs")
        print(f"[SENSOR DEBUG] Pins: Data={data_pin}, Clock={clock_pin}, Latch={latch_pin}")
        
        if self.is_pi5:
            # Pi 5: gebruik lgpio
            print(f"[SENSOR DEBUG] Backend: lgpio")
            self.chip = lgpio.gpiochip_open(0)
            
            # Claim pins
            # Data pin als input met pull-down
            lgpio.gpio_claim_input(self.chip, self.data_pin, lgpio.SET_PULL_DOWN)
            # Clock en latch als output
            lgpio.gpio_claim_output(self.chip, self.clock_pin, 0)  # Start LOW
            lgpio.gpio_claim_output(self.chip, self.latch_pin, 1)  # Start HIGH
            
            print(f"[SENSOR DEBUG] lgpio pins geclaimed")
        else:
            # Oudere Pi's: gebruik RPi.GPIO
            print(f"[SENSOR DEBUG] Backend: RPi.GPIO")
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup pins (data pin met pull-down voor stabiele readings)
            GPIO.setup(self.data_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(self.clock_pin, GPIO.OUT)
            GPIO.setup(self.latch_pin, GPIO.OUT)
            
            # Initiële staat
            GPIO.output(self.clock_pin, GPIO.LOW)
            GPIO.output(self.latch_pin, GPIO.HIGH)
            
            print(f"[SENSOR DEBUG] RPi.GPIO pins geconfigureerd")
        
        print(f"[SENSOR DEBUG] SensorReader succesvol geïnitialiseerd!")
        print("")
    
    def read_all(self):
        """
        Lees alle inputs uit de cascaded shift registers
        
        Returns:
            List van 64 boolean waarden (True = high/magneet gedetecteerd)
        """
        if self.is_pi5:
            # Pi 5: gebruik lgpio
            # Latch de huidige inputs (laad parallel data)
            lgpio.gpio_write(self.chip, self.latch_pin, 0)  # LOW
            time.sleep(0.000001)  # 1 microseconde delay voor stable latch
            lgpio.gpio_write(self.chip, self.latch_pin, 1)  # HIGH
            time.sleep(0.000001)  # 1 microseconde delay na latch
            
            # Lees alle bits uit via shift
            values = []
            for i in range(self.num_inputs):
                # Lees huidige bit
                bit = lgpio.gpio_read(self.chip, self.data_pin)
                values.append(bool(bit))
                
                # Clock puls voor volgende bit
                lgpio.gpio_write(self.chip, self.clock_pin, 1)  # HIGH
                time.sleep(0.000001)  # 1 microseconde clock high time
                lgpio.gpio_write(self.chip, self.clock_pin, 0)  # LOW
                time.sleep(0.000001)  # 1 microseconde clock low time
        else:
            # Oudere Pi's: gebruik RPi.GPIO
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
        if self.is_pi5:
            # Pi 5: sluit lgpio chip
            lgpio.gpio_free(self.chip, self.data_pin)
            lgpio.gpio_free(self.chip, self.clock_pin)
            lgpio.gpio_free(self.chip, self.latch_pin)
            lgpio.gpiochip_close(self.chip)
        else:
            # Oudere Pi's: cleanup RPi.GPIO
            GPIO.cleanup([self.data_pin, self.clock_pin, self.latch_pin])
