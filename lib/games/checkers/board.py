#!/usr/bin/env python3
"""
Checkers Board Renderer

Extends BaseBoardRenderer voor checkers-specifieke rendering.
"""

import pygame
import os
from lib.gui.board import BaseBoardRenderer


class CheckersBoardRenderer(BaseBoardRenderer):
    """Renders checkers board, pieces, and overlays"""
    
    # Checkers kleuren (traditioneel groen/beige)
    COLOR_LIGHT_SQUARE = (240, 217, 181)  # Beige (niet-speelbaar)
    COLOR_DARK_SQUARE = (60, 120, 60)     # Donkergroen (speelbaar)
    
    def __init__(self, screen, board_size, square_size, font_small):
        super().__init__(screen, board_size, square_size, font_small)
        self.piece_images = self._load_piece_images()
    
    def _get_square_notation(self, row, col):
        """Converteer row/col naar chess notatie (a1-h8, lowercase voor checkers)"""
        return f"{chr(97 + col)}{8 - row}"
    
    def _load_piece_images(self):
        """Load checkers piece images"""
        pieces = {}
        piece_types = ['white_man', 'white_king', 'black_man', 'black_king']
        
        for piece_type in piece_types:
            try:
                img_path = os.path.join('assets', 'checkers_pieces', f'{piece_type}.png')
                img = pygame.image.load(img_path)
                pieces[piece_type] = pygame.transform.smoothscale(img, (self.square_size - 10, self.square_size - 10))
            except pygame.error as e:
                print(f"Waarschuwing: Kon {piece_type} image niet laden: {e}")
                # Fallback: teken eenvoudige cirkel
                surf = pygame.Surface((self.square_size - 10, self.square_size - 10), pygame.SRCALPHA)
                color = (255, 255, 255) if 'white' in piece_type else (0, 0, 0)
                pygame.draw.circle(surf, color, (self.square_size // 2 - 5, self.square_size // 2 - 5), self.square_size // 2 - 10)
                if 'king' in piece_type:
                    # Teken kroon indicator
                    pygame.draw.circle(surf, (255, 215, 0), (self.square_size // 2 - 5, self.square_size // 2 - 5), 10)
                pieces[piece_type] = surf
        
        return pieces
    
    def draw_board(self, highlighted_squares=None):
        """
        Teken checkers bord met highlighted squares
        
        Args:
            highlighted_squares: Dict met 'destinations' (groen) en 'intermediate' (geel) keys
                               Of list voor backwards compatibility
        """
        # Parse input
        if isinstance(highlighted_squares, dict):
            destinations = [sq.lower() for sq in highlighted_squares.get('destinations', [])]
            intermediate = [sq.lower() for sq in highlighted_squares.get('intermediate', [])]
        else:
            # Backwards compatible
            destinations = [sq.lower() for sq in (highlighted_squares or [])]
            intermediate = []
        
        # Kleuren voor highlights
        COLOR_INTERMEDIATE = (255, 255, 0)  # Geel voor tussenposities
        
        for row in range(8):
            for col in range(8):
                x = col * self.square_size
                y = row * self.square_size
                
                # Bepaal square kleur (checkerboard pattern)
                is_dark = (row + col) % 2 == 1
                
                square_notation = self._get_square_notation(row, col)
                
                # Kies kleur: geel voor intermediate, groen voor destinations, anders normaal
                if square_notation in intermediate:
                    color = COLOR_INTERMEDIATE
                elif square_notation in destinations:
                    color = self.COLOR_HIGHLIGHT
                else:
                    color = self.COLOR_DARK_SQUARE if is_dark else self.COLOR_LIGHT_SQUARE
                
                pygame.draw.rect(self.screen, color, (x, y, self.square_size, self.square_size))
    
    def draw_coordinates(self):
        """Teken chess coördinaten (A-H, 1-8) - zelfde als chess"""
        for i in range(8):
            # Files (A-H) onderaan op laatste rij
            letter = chr(65 + i)
            x = i * self.square_size + self.square_size - 15
            y = 7 * self.square_size + self.square_size - 20
            
            # Teken zwarte outline (rond de tekst)
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]:
                outline = self.font_small.render(letter, True, self.COLOR_BLACK)
                self.screen.blit(outline, (x + dx, y + dy))
            
            # Teken witte tekst
            label = self.font_small.render(letter, True, self.COLOR_WHITE)
            self.screen.blit(label, (x, y))
            
            # Ranks (1-8) links op eerste kolom
            number = str(8 - i)
            nx = 5
            ny = i * self.square_size + 5
            
            # Teken zwarte outline
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]:
                outline = self.font_small.render(number, True, self.COLOR_BLACK)
                self.screen.blit(outline, (nx + dx, ny + dy))
            
            # Teken witte tekst
            label = self.font_small.render(number, True, self.COLOR_WHITE)
            self.screen.blit(label, (nx, ny))
    
    def draw_pieces(self, board_state):
        """
        Teken checkers pieces
        
        Args:
            board_state: Dict met square notatie -> piece type ('white_man', 'black_king', etc.)
        """
        for square_notation, piece_type in board_state.items():
            if piece_type and piece_type in self.piece_images:
                col = ord(square_notation[0]) - ord('a')
                row = 8 - int(square_notation[1])
                
                x = col * self.square_size + 5
                y = row * self.square_size + 5
                
                self.screen.blit(self.piece_images[piece_type], (x, y))
    
    def get_square_from_pos(self, pos):
        """
        Converteer muis positie naar chess square notatie (lowercase voor checkers)
        
        Args:
            pos: (x, y) tuple van muis positie
            
        Returns:
            String zoals "e2" of None als niet op bord geklikt
        """
        x, y = pos
        
        # Check of klik binnen bord is
        if x < 0 or x >= self.board_size or y < 0 or y >= self.board_size:
            return None
        
        # Converteer naar kolom en rij
        col = x // self.square_size
        row = y // self.square_size
        
        # Converteer naar chess notatie (lowercase)
        return f"{chr(97 + col)}{8 - row}"
    
    def draw_debug_overlays(self, active_sensor_states):
        """
        Override om sensor states met UPPERCASE keys te converteren naar lowercase
        
        Args:
            active_sensor_states: Dict met UPPERCASE square notaties (van ChessMapper)
        """
        # Converteer keys naar lowercase voor checkers
        lowercase_states = {key.lower(): value for key, value in active_sensor_states.items()}
        # Roep parent method aan met lowercase keys
        super().draw_debug_overlays(lowercase_states)

