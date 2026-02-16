#!/usr/bin/env python3
"""
LED Library voor Chess Board

Stuurt 64 RGBW LEDs aan onder het schaakbord voor visuele feedback.
Elk veld heeft een LED die legal moves, selecties en hints kan tonen.

Hardware:
- 64x SK5812 RGBW LEDs (similar to WS2812 maar met dedicated white channel)
- GPIO18 (PWM) via SN74AHCT1G125 3.3V→5V level shifter
- Brightness control via settings (0-100%)

Functionaliteit:
- Individual LED control per veld (A1-H8)
- Color modes: legal moves (groen), selected piece (blauw), hints
- Brightness aanpasbaar via settings
- Clear/reset alle LEDs

Hoofdklasse:
- LEDController: Interface naar rpi_ws281x library met schaakbord mapping
  Automatisch detecteert Raspberry Pi 5 en gebruikt de juiste backend

Wordt gebruikt door: chessgame.py (voor move feedback)
"""

import os


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
                    print(f"[LED DEBUG] Gedetecteerd bord: {model_info}")
                    break
            
            if is_pi5:
                print("[LED DEBUG] → Raspberry Pi 5 gedetecteerd, gebruik adafruit libraries")
            else:
                print("[LED DEBUG] → Oudere Raspberry Pi gedetecteerd, gebruik rpi_ws281x")
            
            return is_pi5
    except Exception as e:
        print(f"[LED DEBUG] Fout bij detectie: {e}, veronderstel oudere Pi")
        return False


# Import de juiste LED bibliotheek afhankelijk van de Pi versie
IS_PI5 = is_raspberry_pi_5()

if IS_PI5:
    # Pi 5 gebruikt adafruit libraries
    import adafruit_pixelbuf
    import board
    from adafruit_raspberry_pi5_neopixel_write import neopixel_write
    
    class Pi5Pixelbuf(adafruit_pixelbuf.PixelBuf):
        """PixelBuf implementatie voor Raspberry Pi 5"""
        def __init__(self, pin, size, **kwargs):
            self._pin = pin
            super().__init__(size=size, **kwargs)

        def _transmit(self, buf):
            neopixel_write(self._pin, buf)
else:
    # Oudere Pi's gebruiken rpi_ws281x
    from rpi_ws281x import PixelStrip


class LEDController:
    """LED controller voor rond schaakbord"""
    
    # Configuratie
    LEDS_PER_KWART = 16
    NUM_KWARTEN = 4
    GPIO_PIN = 12
    
    def __init__(self, pin=GPIO_PIN, brightness=255):
        """
        Initialiseer LED strip
        
        Args:
            pin: GPIO pin nummer (BCM)
            brightness: Helderheid (0-255), default 128 (50%)
        """
        self.num_kwarten = self.NUM_KWARTEN
        self.led_count = self.LEDS_PER_KWART * self.num_kwarten
        self.is_pi5 = IS_PI5
        
        # Clamp brightness to valid range (0-255)
        brightness = max(0, min(255, int(brightness)))
        self.brightness = brightness
        
        print(f"[LED DEBUG] Initialiseer LEDController met {self.led_count} LEDs")
        print(f"[LED DEBUG] Brightness: {brightness}/255 ({brightness/255*100:.1f}%)")
        
        if self.is_pi5:
            # Pi 5: gebruik adafruit libraries
            print(f"[LED DEBUG] Backend: Adafruit Pi5 (board.D12, RBG)")
            self.pin = board.D12  # GPIO12
            self.strip = Pi5Pixelbuf(
                self.pin, 
                self.led_count, 
                auto_write=False,  # Buffering voor performance
                byteorder="RBG"   # RBG: Red, Blue, Green
            )
            print(f"[LED DEBUG] Pi5Pixelbuf geïnitialiseerd op GPIO12 (RBG, auto_write=False)")
            # Brightness wordt handmatig gedaan bij Pi5
        else:
            # Oudere Pi's: gebruik rpi_ws281x
            print(f"[LED DEBUG] Backend: rpi_ws281x (GPIO{pin})")
            self.strip = PixelStrip(self.led_count, pin)
            self.strip.begin()
            self.strip.setBrightness(brightness)
            print(f"[LED DEBUG] PixelStrip geïnitialiseerd op GPIO{pin}")
        
        self.clear()
        print(f"[LED DEBUG] LEDController succesvol geïnitialiseerd!")
        print("")
    
    def set_led(self, led_num, red, green, blue, white=0):
        """
        Zet een enkele LED
        
        Args:
            led_num: LED nummer (0-63)
            red: Rood (0-255)
            green: Groen (0-255)
            blue: Blauw (0-255)
            white: Wit (0-255)
        """
        if 0 <= led_num < self.led_count:
            if self.is_pi5:
                # Pi 5: gebruik PixelBuf indexing met RBG order
                # Pas brightness handmatig toe
                brightness_factor = self.brightness / 255.0
                r = int(red * brightness_factor)
                g = int(green * brightness_factor)
                b = int(blue * brightness_factor)
                # RBG byteorder met omgewisselde r/g: Green, Blue, Red
                self.strip[led_num] = (g, b, r)
            else:
                # Oudere Pi's: gebruik rpi_ws281x
                # Compenseer voor lage brightness settings
                current_brightness = self.strip.getBrightness()
                brightness_factor = current_brightness / 255.0
                
                # Als effectieve brightness < 3%, schaal dan de kleuren op
                MIN_EFFECTIVE_BRIGHTNESS = 0.03  # 3%
                if brightness_factor < MIN_EFFECTIVE_BRIGHTNESS and brightness_factor > 0:
                    # Bereken schaalfactor om 3% te bereiken
                    scale = MIN_EFFECTIVE_BRIGHTNESS / brightness_factor
                    red = min(255, int(red * scale))
                    green = min(255, int(green * scale))
                    blue = min(255, int(blue * scale))
                    white = min(255, int(white * scale))
                
                color = (white << 24) | (red << 16) | (green << 8) | blue
                self.strip.setPixelColor(led_num, color)
    
    def show(self):
        """Update de LEDs (maak de wijzigingen zichtbaar)"""
        if self.is_pi5:
            self.strip.show()
        else:
            self.strip.show()
    
    def set_brightness(self, brightness_percent):
        """Zet brightness (0-100%)"""
        brightness_value = int((brightness_percent / 100) * 255)
        brightness_value = max(0, min(255, brightness_value))  # Clamp to 0-255
        self.brightness = brightness_value
        
        if not self.is_pi5:
            # Alleen voor oudere Pi's
            self.strip.setBrightness(brightness_value)
    
    def clear(self):
        """Zet alle LEDs uit"""
        if self.is_pi5:
            # BGR format: (blue, green, red)
            self.strip.fill((0, 0, 0))
            self.strip.show()
        else:
            for i in range(self.led_count):
                self.strip.setPixelColor(i, 0)
            self.strip.show()
    
    def set_all(self, red, green, blue, white=0):
        """Zet alle LEDs op dezelfde kleur"""
        for i in range(self.led_count):
            self.set_led(i, red, green, blue, white)
        self.show()
    
    def get_led_count(self):
        """Geef totaal aantal LEDs terug"""
        return self.led_count
    
    def cleanup(self):
        """Cleanup: zet alle LEDs uit"""
        self.clear()
