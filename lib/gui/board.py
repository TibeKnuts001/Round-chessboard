#!/usr/bin/env python3
"""
Base Board Renderer

Tekent het basis 8x8 board met:
- Afwisselende light/dark squares
- Square highlights
- Selection indicators
- Debug overlays

Game-specifieke renderers extenden deze class voor:
- Piece rendering
- Coördinaat labels
- Specifieke kleuren
"""

import pygame


class BaseBoardRenderer:
    """Base class voor board rendering"""
    
    # Default kleuren (kunnen worden overschreven)
    COLOR_LIGHT_SQUARE = (240, 217, 181)
    COLOR_DARK_SQUARE = (181, 136, 99)
    COLOR_HIGHLIGHT = (186, 202, 68)  # Groen voor normale moves
    COLOR_CAPTURE = (220, 80, 80)  # Rood voor captures
    COLOR_SELECTION = (255, 215, 0)
    COLOR_WHITE = (255, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    
    def __init__(self, screen, board_size, square_size, font_small):
        """
        Args:
            screen: Pygame screen surface
            board_size: Grootte van het bord in pixels
            square_size: Grootte van één veld in pixels
            font_small: Font voor coordinaten
        """
        self.screen = screen
        self.board_size = board_size
        self.square_size = square_size
        self.font_small = font_small
        self.font = pygame.font.Font(None, 36)
    
    def draw_board_grid(self, highlighted_squares, selected_square, capture_squares=None):
        """
        Teken het basis 8x8 grid met highlights
        
        Args:
            highlighted_squares: List van square notaties voor normale moves
            selected_square: Notatie van geselecteerd veld of None
            capture_squares: List van square notaties voor captures (rood)
        """
        if capture_squares is None:
            capture_squares = []
        
        for row in range(8):
            for col in range(8):
                # Bepaal kleur
                is_light = (row + col) % 2 == 0
                color = self.COLOR_LIGHT_SQUARE if is_light else self.COLOR_DARK_SQUARE
                
                # Check of veld highlighted moet zijn
                square_notation = self._get_square_notation(row, col)
                
                # Capture squares krijgen rode achtergrond
                if square_notation in capture_squares:
                    color = self.COLOR_CAPTURE
                # Normale move squares krijgen groene achtergrond
                elif square_notation in highlighted_squares:
                    color = self.COLOR_HIGHLIGHT
                
                # Teken veld
                rect = pygame.Rect(
                    col * self.square_size,
                    row * self.square_size,
                    self.square_size,
                    self.square_size
                )
                pygame.draw.rect(self.screen, color, rect)
                
                # Teken selectie indicator (gouden knipperende cirkel)
                if selected_square and square_notation == selected_square:
                    self._draw_selection_indicator(col, row)
    
    def draw_highlights(self, highlighted_squares, selected_square, capture_squares=None, tutorial_squares=None):
        """
        Teken alleen de highlights/selections bovenop bestaand board
        Gebruikt voor efficient caching: board grid cached, alleen highlights hertekenen
        
        Args:
            highlighted_squares: List van square notaties voor normale moves
            selected_square: Notatie van geselecteerd veld of None
            capture_squares: List van square notaties voor captures (rood)
            tutorial_squares: Dict van {square: (r, g, b)} voor tutorial mode
        """
        if capture_squares is None:
            capture_squares = []
        if tutorial_squares is None:
            tutorial_squares = {}
        
        for row in range(8):
            for col in range(8):
                square_notation = self._get_square_notation(row, col)
                
                # Teken overlay alleen als er een highlight is
                if square_notation in tutorial_squares:
                    # Tutorial squares have custom colors
                    overlay = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    color = tutorial_squares[square_notation]
                    overlay.fill((*color, 180))  # 70% transparency for tutorial
                    self.screen.blit(overlay, (col * self.square_size, row * self.square_size))
                elif square_notation in capture_squares or square_notation in highlighted_squares:
                    # Semi-transparent overlay
                    overlay = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    
                    if square_notation in capture_squares:
                        overlay.fill((*self.COLOR_CAPTURE, 128))  # 50% transparency
                    elif square_notation in highlighted_squares:
                        overlay.fill((*self.COLOR_HIGHLIGHT, 128))
                    
                    self.screen.blit(overlay, (col * self.square_size, row * self.square_size))
                
                # Teken selectie indicator
                if selected_square and square_notation == selected_square:
                    self._draw_selection_indicator(col, row)
    
    def _draw_selection_indicator(self, col, row):
        """Teken selectie indicator met knippereffect"""
        blink_on = (pygame.time.get_ticks() // 500) % 2 == 0
        
        if blink_on:
            center_x = col * self.square_size + self.square_size // 2
            center_y = row * self.square_size + self.square_size // 2
            radius = self.square_size // 2 - 5
            
            # Teken dikke cirkel
            for i in range(5):
                pygame.draw.circle(
                    self.screen,
                    self.COLOR_SELECTION,
                    (center_x, center_y),
                    radius - i,
                    1
                )
    
    def draw_debug_overlays(self, active_sensor_states):
        """
        Teken debug overlays voor sensor detection
        
        Args:
            active_sensor_states: Dict met square notaties en sensor states
        """
        for row in range(8):
            for col in range(8):
                square_notation = self._get_square_notation(row, col)
                
                if square_notation in active_sensor_states and active_sensor_states[square_notation]:
                    center_x = col * self.square_size + self.square_size // 2
                    center_y = row * self.square_size + self.square_size // 2
                    
                    indicator_radius = 18
                    
                    # Gele cirkel met M voor magneet
                    pygame.draw.circle(self.screen, (255, 215, 0), (center_x, center_y), indicator_radius)
                    pygame.draw.circle(self.screen, (200, 170, 0), (center_x, center_y), indicator_radius, 2)
                    
                    magnet_text = self.font.render("M", True, self.COLOR_BLACK)
                    text_rect = magnet_text.get_rect(center=(center_x, center_y))
                    self.screen.blit(magnet_text, text_rect)
    
    def get_square_from_pos(self, pos):
        """
        Converteer muis positie naar square notatie
        Moet worden geïmplementeerd door subclass
        
        Args:
            pos: (x, y) tuple van muis positie
            
        Returns:
            String met square notatie of None
        """
        raise NotImplementedError("Subclass must implement get_square_from_pos()")
    
    def _get_square_notation(self, row, col):
        """
        Converteer row/col naar square notatie
        Moet worden geïmplementeerd door subclass
        
        Args:
            row: Row index (0-7)
            col: Column index (0-7)
            
        Returns:
            String met square notatie (bijv "E2" voor chess of "12" voor checkers)
        """
        raise NotImplementedError("Subclass must implement _get_square_notation()")
