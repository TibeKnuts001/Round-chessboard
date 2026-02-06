#!/usr/bin/env python3
"""
Screensaver Module

Displays static splash screen with animated overlay effects.
Features particles, color waves, and scanlines.
"""

import pygame
import math
import os
import random


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
    
    def __init__(self, screen, splash_image_path):
        """
        Initialize screensaver
        
        Args:
            screen: Pygame screen surface
            splash_image_path: Path to splash image
        """
        self.screen = screen
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
        
        # Animation state
        self.time = 0.0
        self.animation_speed = 1.0
        
        # Floating particles - subtiel
        self.particles = [Particle(self.screen_width, self.screen_height) for _ in range(100)]
        
        # Scanline position and timing
        self.scanline_y = -1000  # Start offscreen
        self.scanline_waiting = True
        self.next_scanline_time = 15.0  # Wait 15 seconds before first scanline
        
    def update(self, dt):
        """
        Update animation state
        
        Args:
            dt: Delta time since last frame (seconds)
        """
        self.time += dt * self.animation_speed
        
        # Update particles
        for particle in self.particles:
            particle.update(dt)
        
        # Update scanline - only appears every 15 seconds
        if self.scanline_waiting:
            # Waiting for next scanline
            self.next_scanline_time -= dt
            if self.next_scanline_time <= 0:
                # Start new scanline
                self.scanline_waiting = False
                self.scanline_y = 0
        else:
            # Scanline is moving
            self.scanline_y += 150 * dt
            if self.scanline_y > self.screen_height + 50:
                # Scanline finished, wait 15 seconds before next one
                self.scanline_waiting = True
                self.next_scanline_time = 15.0
                self.scanline_y = -1000  # Move offscreen
        
    def draw(self):
        """Draw static image with animated overlay effects"""
        # Black background
        self.screen.fill((0, 0, 0))
        
        # Draw static splash image (centered, no movement)
        self.screen.blit(self.splash_image, self.splash_rect)
        
        # Effect 1: Floating particles
        self._draw_particles()
        
        # Effect 2: Color wave overlay
        self._draw_color_wave()
        
        # Effect 3: Scanline sweep
        self._draw_scanline()
        
        # Effect 4: Pulsing corner glow
        self._draw_corner_glow()
    
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
        """Draw moving scanline effect"""
        scanline_surf = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        
        # Main scanline - subtiel
        for i in range(50):
            alpha = int(40 * (1 - i / 50.0))
            y = int(self.scanline_y - i)
            if 0 <= y < self.screen_height:
                pygame.draw.line(scanline_surf, (100, 200, 255, alpha), 
                               (0, y), (self.screen_width, y), 1)
        
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
