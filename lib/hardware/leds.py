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

Wordt gebruikt door: chessgame.py (voor move feedback)
"""

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
        self.strip = PixelStrip(self.led_count, pin)
        self.strip.begin()
        # Clamp brightness to valid range (0-255)
        brightness = max(0, min(255, int(brightness)))
        self.strip.setBrightness(brightness)
        self.clear()
    
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
            color = (white << 24) | (red << 16) | (green << 8) | blue
            self.strip.setPixelColor(led_num, color)
    
    def show(self):
        """Update de LEDs (maak de wijzigingen zichtbaar)"""
        self.strip.show()
    
    def set_brightness(self, brightness_percent):
        """Zet brightness (0-100%)"""
        brightness_value = int((brightness_percent / 100) * 255)
        brightness_value = max(0, min(255, brightness_value))  # Clamp to 0-255
        self.strip.setBrightness(brightness_value)
    
    def clear(self):
        """Zet alle LEDs uit"""
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
