#!/usr/bin/env python3
"""
Base Sidebar Renderer

Tekent de basis sidebar elementen:
- Background
- Title area
- Button rendering

Game-specifieke sidebars extenden deze class voor:
- Game status info
- Captured pieces display
- Move history
"""

import pygame
from lib.gui.widgets import UIWidgets


class BaseSidebarRenderer:
    """Base class voor sidebar rendering"""
    
    # Default kleuren
    COLOR_SIDEBAR = (240, 240, 240)
    COLOR_BLACK = (0, 0, 0)
    COLOR_WHITE = (255, 255, 255)
    COLOR_BUTTON = (70, 130, 180)
    COLOR_BUTTON_HOVER = (100, 149, 237)
    
    def __init__(self, screen, board_size, sidebar_width, screen_height, font, font_small):
        """
        Args:
            screen: Pygame screen surface
            board_size: Grootte van het bord in pixels (voor x offset)
            sidebar_width: Breedte van de sidebar
            screen_height: Hoogte van het scherm
            font: Grote font
            font_small: Kleine font
        """
        self.screen = screen
        self.board_size = board_size
        self.sidebar_width = sidebar_width
        self.screen_height = screen_height
        self.font = font
        self.font_small = font_small
    
    def draw_background(self):
        """Teken sidebar achtergrond"""
        sidebar_rect = pygame.Rect(self.board_size, 0, self.sidebar_width, self.screen_height)
        pygame.draw.rect(self.screen, self.COLOR_SIDEBAR, sidebar_rect)
        
        # Teken verticale scheidingslijn tussen bord en sidebar
        pygame.draw.line(self.screen, (0, 0, 0), 
                        (self.board_size, 0), 
                        (self.board_size, self.screen_height), 
                        4)
    
    def draw_title(self, title_text):
        """
        Teken title bovenaan sidebar
        
        Args:
            title_text: String voor de title
            
        Returns:
            y_offset voor volgende elementen
        """
        title = self.font.render(title_text, True, self.COLOR_BLACK)
        title_rect = title.get_rect(center=(self.board_size + self.sidebar_width // 2, 30))
        self.screen.blit(title, title_rect)
        return 70  # Start y voor content
    
    def draw_buttons(self, new_game_button, exit_button, settings_button, undo_button=None, game_started=False, can_undo=False):
        """Teken alle control buttons met UIWidgets"""
        # Button text: "Stop Game" als spel bezig is, anders "New Game"
        new_game_text = "Stop Game" if game_started else "New Game"
        
        # New Game / Stop Game button
        # Als game niet gestart: volle breedte
        # Als game gestart: normale breedte (naast undo)
        if game_started:
            # Stop Game button (normale breedte)
            UIWidgets.draw_button(self.screen, new_game_button, new_game_text, self.font_small, is_primary=True)
            # Undo button (naast Stop Game)
            if undo_button:
                UIWidgets.draw_button(self.screen, undo_button, "Undo", self.font_small, is_primary=False, disabled=not can_undo)
        else:
            # New Game button (volle breedte)
            full_width_rect = pygame.Rect(
                new_game_button.x,
                new_game_button.y,
                new_game_button.width * 2 + 10,  # 2x breedte + spacing
                new_game_button.height
            )
            UIWidgets.draw_button(self.screen, full_width_rect, new_game_text, self.font_small, is_primary=True)
        
        UIWidgets.draw_button(self.screen, settings_button, "Settings", self.font_small, is_primary=False)
        UIWidgets.draw_button(self.screen, exit_button, "Exit", self.font_small, is_primary=False, is_danger=True)
    
    def draw_text_line(self, text, y_offset, bold=False):
        """
        Teken een regel tekst
        
        Args:
            text: Tekst om te tekenen
            y_offset: Y positie
            bold: Of het bold moet zijn
            
        Returns:
            Nieuwe y_offset na deze regel
        """
        font_to_use = self.font if bold else self.font_small
        text_surf = font_to_use.render(text, True, self.COLOR_BLACK)
        self.screen.blit(text_surf, (self.board_size + 20, y_offset))
        return y_offset + 30
