#!/usr/bin/env python3
"""
Screensaver Module

Displays static splash screen with animated overlay effects.
Features particles, color waves, and scanlines.
Animations only on Raspberry Pi 4 or higher (performance).
"""

import pygame
import math
import os
import random


def get_raspberry_pi_version():
    """Detecteer Raspberry Pi versie (retourneert 3, 4, 5, etc. of 0 voor onbekend)"""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            
            # Extract model info
            for line in cpuinfo.split('\n'):
                if line.startswith('Model'):
                    model_info = line.split(':', 1)[1].strip()
                    print(f"[SCREENSAVER DEBUG] Gedetecteerd bord: {model_info}")
                    
                    # Bepaal versie nummer
                    if 'Raspberry Pi 5' in model_info:
                        version = 5
                    elif 'Raspberry Pi 4' in model_info:
                        version = 4
                    elif 'Raspberry Pi 3' in model_info:
                        version = 3
                    elif 'Raspberry Pi 2' in model_info:
                        version = 2
                    elif 'Raspberry Pi' in model_info:
                        version = 1
                    else:
                        version = 0
                    
                    if version >= 4:
                        print(f"[SCREENSAVER DEBUG] → Pi {version}: Animaties ENABLED")
                    else:
                        print(f"[SCREENSAVER DEBUG] → Pi {version}: Animaties DISABLED (statisch beeld)")
                    
                    return version
            
            return 0
    except Exception as e:
        print(f"[SCREENSAVER DEBUG] Fout bij detectie: {e}, veronderstel oudere Pi")
        return 0


# Detecteer Pi versie globaal
PI_VERSION = get_raspberry_pi_version()
ENABLE_ANIMATIONS = PI_VERSION >= 4  # Alleen Pi 4 en hoger


class Particle:
    """Floating particle for screensaver effect"""
    def __init__(self, screen_width, screen_height):
        self.x = random.uniform(0, screen_width)
        self.y = random.uniform(0, screen_height)
        self.vx = random.uniform(-20, 20)
        self.vy = random.uniform(-20, 20)
        self.size = random.uniform(1, 3)
        self.alpha = random.randint(30, 100)
        self.screen_width = screen_width
        self.screen_height = screen_height
        
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Wrap around screen
        if self.x < 0:
            self.x = self.screen_width
        elif self.x > self.screen_width:
            self.x = 0
        if self.y < 0:
            self.y = self.screen_height
        elif self.y > self.screen_height:
            self.y = 0


class Screensaver:
    """Animated screensaver with static splash image and dynamic effects"""
    
    def __init__(self, screen, splash_image_path, settings):
        """
        Initialize screensaver
        
        Args:
            screen: Pygame screen surface
            splash_image_path: Path to splash image
            settings: Settings instance voor configuratie
        """
        self.screen = screen
        self.settings = settings
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # Load splash image
        if os.path.exists(splash_image_path):
            self.splash_image = pygame.image.load(splash_image_path).convert_alpha()
        else:
            # Fallback: create simple placeholder
            self.splash_image = pygame.Surface((1024, 614))
            self.splash_image.fill((40, 40, 40))
            font = pygame.font.Font(None, 72)
            text = font.render("Screensaver", True, (200, 200, 200))
            text_rect = text.get_rect(center=(512, 307))
            self.splash_image.blit(text, text_rect)
        
        # Center and scale splash image to fit screen nicely
        self.splash_rect = self.splash_image.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        
        # Check of animaties enabled zijn (alleen Pi 4+)
        self.animations_enabled = ENABLE_ANIMATIONS
        
        # Animation state (alleen als enabled)
        if self.animations_enabled:
            self.time = 0.0
            self.animation_speed = 1.0
            
            # Floating particles - subtiel
            self.particles = [Particle(self.screen_width, self.screen_height) for _ in range(100)]
            
            # Scanline position and timing
            self.scanline_x = -self.screen_height  # Start offscreen left
            self.scanline_waiting = True
            self.next_scanline_time = 15.0  # Wait 15 seconds before first scanline
        else:
            # Geen animaties - alleen statisch beeld
            self.time = 0.0
            self.particles = []
            print("[SCREENSAVER] Statische modus (geen animaties)")
        
        # Audio
        self.audio_playing = False
        
    def start_audio(self):
        """Start screensaver audio"""
        # Check of audio enabled is in settings
        if not self.settings.get('screensaver_audio', True, section='general'):
            print("Screensaver audio uitgeschakeld in settings")
            return
        
        try:
            if not self.audio_playing:
                pygame.mixer.init()
                pygame.mixer.music.load("assets/audio/screensaver.mp3")
                pygame.mixer.music.play(-1)  # Loop forever
                self.audio_playing = True
                print("✓ Screensaver audio gestart")
        except Exception as e:
            print(f"✗ Kon screensaver audio niet starten: {e}")
    
    def stop_audio(self):
        """Stop screensaver audio"""
        try:
            if self.audio_playing:
                pygame.mixer.music.stop()
                self.audio_playing = False
                print("✓ Screensaver audio gestopt")
        except Exception as e:
            print(f"✗ Kon screensaver audio niet stoppen: {e}")
        
    def update(self, dt):
        """
        Update animation state
        
        Args:
            dt: Delta time since last frame (seconds)
        """
        # Skip updates als animaties niet enabled zijn
        if not self.animations_enabled:
            return
        
        self.time += dt * self.animation_speed
        
        # Update particles
        for particle in self.particles:
            particle.update(dt)
        
        # Update scanline - diagonal movement, only appears every 15 seconds
        if self.scanline_waiting:
            # Waiting for next scanline
            self.next_scanline_time -= dt
            if self.next_scanline_time <= 0:
                # Start new scanline from left
                self.scanline_waiting = False
                self.scanline_x = -self.screen_height
        else:
            # Scanline is moving left to right
            self.scanline_x += 150 * dt
            # Stop when completely off screen on the right
            if self.scanline_x > self.screen_width + self.screen_height:
                # Scanline finished, wait 15 seconds before next one
                self.scanline_waiting = True
                self.next_scanline_time = 15.0
                self.scanline_x = -self.screen_height
        
    def draw(self):
        """Draw static image with animated overlay effects"""
        # Black background
        self.screen.fill((0, 0, 0))
        
        # Draw static splash image (centered, no movement) - ALTIJD
        self.screen.blit(self.splash_image, self.splash_rect)
        
        # Alleen animaties tekenen als enabled (Pi 4+)
        if self.animations_enabled:
            # Effect 1: Floating particles
            self._draw_particles()
            
            # Effect 2: Color wave overlay
            self._draw_color_wave()
            
            # Effect 3: Pulsing corner glow
            self._draw_corner_glow()
            
            # Effect 4: Scanline sweep (drawn last so it's on top)
            self._draw_scanline()
    
    def _draw_particles(self):
        """Draw floating particles"""
        particle_surf = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        
        for particle in self.particles:
            # Draw particle with subtle glow
            color = (200, 220, 255, particle.alpha)
            pygame.draw.circle(particle_surf, color, (int(particle.x), int(particle.y)), int(particle.size))
            # Small glow
            glow_color = (150, 180, 255, particle.alpha // 2)
            pygame.draw.circle(particle_surf, glow_color, (int(particle.x), int(particle.y)), int(particle.size * 2))
        
        self.screen.blit(particle_surf, (0, 0))
    
    def _draw_color_wave(self):
        """Draw animated color gradient wave"""
        wave_surf = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        
        # Create vertical gradient waves - FELLER
        for y in range(0, self.screen_height, 4):
            # Wave offset
            wave_offset = math.sin((y / 100.0) + self.time * 2) * 50
            # Color based on position and time
            hue = (y / self.screen_height + self.time * 0.1) % 1.0
            
            # Convert HSV-like to RGB (simplified) - VEEL FELLER
            if hue < 0.33:
                r = max(0, min(255, int(200 * (1 - hue * 3))))
                g = max(0, min(255, int(200 * hue * 3)))
                b = 255
            elif hue < 0.66:
                r = 0
                g = max(0, min(255, int(200 * (1 - (hue - 0.33) * 3))))
                b = max(0, min(255, int(255 - 150 * (hue - 0.33) * 3)))
            else:
                r = max(0, min(255, int(200 * (hue - 0.66) * 3)))
                g = 0
                b = max(0, min(255, int(200 * (1 - (hue - 0.66) * 3))))
            
            alpha = max(0, min(255, int(15 + 10 * math.sin(self.time + y / 50.0))))
            pygame.draw.rect(wave_surf, (r, g, b, alpha), 
                           (int(wave_offset), y, self.screen_width, 4))
        
        self.screen.blit(wave_surf, (0, 0))
    
    def _draw_scanline(self):
        """Draw moving diagonal scanline effect with grainy texture"""
        # Only draw if scanline is visible
        if self.scanline_waiting:
            return
    def _draw_scanline(self):
        """Draw moving diagonal scanline effect - subtle like original but diagonal"""
        # Only draw if scanline is visible
        if self.scanline_waiting:
            return
        
        scanline_surf = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        
        offset = int(self.scanline_x)
        
        # Single diagonal line with subtle trail (like original horizontal scanline)
        for i in range(50):
            alpha = int(40 * (1 - i / 50.0))
            
            # Diagonal line position - each line slightly behind the main one
            x_offset = offset - i
            
            # Draw diagonal line from top to bottom
            start_x = x_offset - self.screen_height
            start_y = 0
            end_x = x_offset + self.screen_height
            end_y = self.screen_height
            
            pygame.draw.line(scanline_surf, (100, 200, 255, alpha), 
                           (start_x, start_y), (end_x, end_y), 1)
        
        self.screen.blit(scanline_surf, (0, 0))
    
    def _draw_corner_glow(self):
        """Draw pulsing glow in corners"""
        glow_surf = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        
        # Pulse intensity - subtiel
        intensity = int(20 + 15 * math.sin(self.time * 1.5))
        
        # Draw radial gradients in corners
        corner_size = 400
        for corner_x, corner_y in [(0, 0), (self.screen_width, 0), 
                                     (0, self.screen_height), (self.screen_width, self.screen_height)]:
            for radius in range(corner_size, 0, -20):
                alpha = int((1 - radius / corner_size) * intensity)
                pygame.draw.circle(glow_surf, (80, 120, 200, alpha), 
                                 (corner_x, corner_y), radius)
        
        self.screen.blit(glow_surf, (0, 0))
