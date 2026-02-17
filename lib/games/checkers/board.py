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
        # Track welke kleur gespiegeld moet worden (rechts na rotatie)
        self.rotated_color = None
    
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
    
    def detect_rotated_color(self, board_state):
        """
        Detecteer welke kleur rechts staat (na 90° rotatie = rijen 6,7,8)
        en stel deze in als rotated_color
        
        Args:
            board_state: Dict met square notatie -> piece type
        """
        # Rijen 6,7,8 komen na rotatie rechts te staan
        white_count = 0
        black_count = 0
        
        for row_num in ['6', '7', '8']:
            for col_letter in 'abcdefgh':
                square_notation = f"{col_letter}{row_num}"
                piece_type = board_state.get(square_notation)
                if piece_type:
                    if piece_type.startswith('white'):
                        white_count += 1
                    elif piece_type.startswith('black'):
                        black_count += 1
        
        # Stel rotated_color in
        if white_count > black_count:
            self.rotated_color = 'white'
            print(f"Checkers: Detected white on right side - will rotate white pieces 180°")
        elif black_count > white_count:
            self.rotated_color = 'black'
            print(f"Checkers: Detected black on right side - will rotate black pieces 180°")
        else:
            self.rotated_color = None
            print(f"Checkers: No clear color on right - no rotation")
    
    def draw_board(self, highlighted_squares=None, last_move=None):
        """
        Teken checkers bord met highlighted squares en last move
        
        Args:
            highlighted_squares: Dict met 'destinations' (groen) en 'intermediate' (geel) keys
                               Of list voor backwards compatibility
            last_move: Tuple (from_square, to_square, intermediate_list) van laatste zet voor subtiele highlighting
        """
        # Parse input
        if isinstance(highlighted_squares, dict):
            destinations = [sq.lower() for sq in highlighted_squares.get('destinations', [])]
            intermediate = [sq.lower() for sq in highlighted_squares.get('intermediate', [])]
        else:
            # Backwards compatible
            destinations = [sq.lower() for sq in (highlighted_squares or [])]
            intermediate = []
        
        # Parse last move (inclusief intermediate squares)
        last_move_squares = []
        last_move_intermediate = []
        if last_move:
            if len(last_move) >= 2:
                last_move_squares = [last_move[0].lower(), last_move[1].lower()]
            if len(last_move) >= 3 and last_move[2]:  # Intermediate squares
                last_move_intermediate = [sq.lower() for sq in last_move[2]]
        
        # Kleuren voor highlights
        COLOR_INTERMEDIATE = (255, 255, 0)  # Geel voor tussenposities
        COLOR_LAST_MOVE = (200, 180, 140)  # Subtiel beige/goud voor laatste zet
        COLOR_LAST_MOVE_INTERMEDIATE = (160, 150, 120)  # Nog subtieler voor intermediate van laatste zet
        
        for row in range(8):
            for col in range(8):
                x = col * self.square_size
                y = row * self.square_size
                
                # Bepaal square kleur (checkerboard pattern)
                is_dark = (row + col) % 2 == 1
                
                square_notation = self._get_square_notation(row, col)
                
                # Kies kleur: prioriteit: intermediate > destinations > last_move > last_move_intermediate > normaal
                if square_notation in intermediate:
                    color = COLOR_INTERMEDIATE
                elif square_notation in destinations:
                    color = self.COLOR_HIGHLIGHT
                elif square_notation in last_move_squares:
                    color = COLOR_LAST_MOVE
                elif square_notation in last_move_intermediate:
                    color = COLOR_LAST_MOVE_INTERMEDIATE
                else:
                    color = self.COLOR_DARK_SQUARE if is_dark else self.COLOR_LIGHT_SQUARE
                
                pygame.draw.rect(self.screen, color, (x, y, self.square_size, self.square_size))
    
    def draw_highlights(self, highlighted_squares=None, last_move=None, tutorial_squares=None):
        """
        Teken alleen highlights bovenop gecached board (voor efficiency)
        
        Args:
            highlighted_squares: Dict met 'destinations' en 'intermediate' keys
            last_move: Tuple (from_square, to_square, intermediate_list)
            tutorial_squares: Dict van {square: (r, g, b)} voor tutorial mode
        """
        if tutorial_squares is None:
            tutorial_squares = {}
        
        # Convert tutorial_squares keys to lowercase for matching
        tutorial_squares = {sq.lower(): color for sq, color in tutorial_squares.items()}
        
        # Parse input
        if isinstance(highlighted_squares, dict):
            destinations = [sq.lower() for sq in highlighted_squares.get('destinations', [])]
            intermediate = [sq.lower() for sq in highlighted_squares.get('intermediate', [])]
        else:
            destinations = [sq.lower() for sq in (highlighted_squares or [])]
            intermediate = []
        
        # Parse last move
        last_move_squares = []
        last_move_intermediate = []
        if last_move:
            if len(last_move) >= 2:
                last_move_squares = [last_move[0].lower(), last_move[1].lower()]
            if len(last_move) >= 3 and last_move[2]:
                last_move_intermediate = [sq.lower() for sq in last_move[2]]
        
        # Kleuren
        COLOR_INTERMEDIATE = (255, 255, 0, 128)
        COLOR_LAST_MOVE = (200, 180, 140, 100)
        COLOR_LAST_MOVE_INTERMEDIATE = (160, 150, 120, 80)
        
        for row in range(8):
            for col in range(8):
                square_notation = self._get_square_notation(row, col)
                
                # Teken overlay alleen als highlight nodig
                overlay = None
                if square_notation in tutorial_squares:
                    # Tutorial mode: gebruik custom color
                    overlay = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    color = tutorial_squares[square_notation]
                    overlay.fill((*color, 180))  # 70% transparency
                elif square_notation in intermediate:
                    overlay = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    overlay.fill(COLOR_INTERMEDIATE)
                elif square_notation in destinations:
                    overlay = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    overlay.fill((*self.COLOR_HIGHLIGHT, 128))
                elif square_notation in last_move_squares:
                    overlay = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    overlay.fill(COLOR_LAST_MOVE)
                elif square_notation in last_move_intermediate:
                    overlay = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                    overlay.fill(COLOR_LAST_MOVE_INTERMEDIATE)
                
                if overlay:
                    self.screen.blit(overlay, (col * self.square_size, row * self.square_size))
    
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
                
                # Haal image op
                image = self.piece_images[piece_type]
                
                # Roteer pieces van de kleur die rechts staat 180 graden
                piece_color = piece_type.split('_')[0]  # 'white' of 'black'
                if self.rotated_color is not None and piece_color == self.rotated_color:
                    image = pygame.transform.rotate(image, 180)
                
                x = col * self.square_size + 5
                y = row * self.square_size + 5
                
                self.screen.blit(image, (x, y))
    
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

