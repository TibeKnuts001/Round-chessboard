#!/usr/bin/env python3
"""
Chess Board Rendering Module

Chess-specifieke board rendering met:
- Chess piece rendering via PNG sprites
- Chess coordinate labels (A-H, 1-8)
"""

import os
import pygame
import chess
from lib.gui.board import BaseBoardRenderer


class ChessBoardRenderer(BaseBoardRenderer):
    """Tekent chess pieces en coördinaten"""
    
    def __init__(self, screen, board_size, square_size, font_small):
        super().__init__(screen, board_size, square_size, font_small)
        # Laad chess piece images
        self.piece_images = self._load_piece_images()
        # Track welke kleur gespiegeld moet worden (rechts na rotatie)
        self.rotated_color = None
    
    def _load_piece_images(self):
        """
        Laad en schaal chess piece images
        
        Returns:
            Dict met piece symbols als keys en pygame surfaces als values
        """
        # Piece mapping: python-chess symbol -> filename
        piece_files = {
            'P': 'white_pawn.png',
            'N': 'white_knight.png',
            'B': 'white_bishop.png',
            'R': 'white_rook.png',
            'Q': 'white_queen.png',
            'K': 'white_king.png',
            'p': 'black_pawn.png',
            'n': 'black_knight.png',
            'b': 'black_bishop.png',
            'r': 'black_rook.png',
            'q': 'black_queen.png',
            'k': 'black_king.png',
        }
        
        # Target size: 75% van square size voor mooie padding
        target_size = int(self.square_size * 0.75)
        
        # Load en schaal images
        images = {}
        # Navigate to assets from lib/games/chess/board.py
        assets_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            'assets',
            'chess_pieces'
        )
        
        for symbol, filename in piece_files.items():
            filepath = os.path.join(assets_path, filename)
            
            # Check of file bestaat
            if not os.path.exists(filepath):
                raise FileNotFoundError(
                    f"Chess piece image niet gevonden: {filepath}\n"
                    f"Plaats de PNG files in assets/chess_pieces/\n"
                    f"Zie assets/README.txt voor details."
                )
            
            # Laad en schaal image
            image = pygame.image.load(filepath)
            scaled_image = pygame.transform.smoothscale(image, (target_size, target_size))
            images[symbol] = scaled_image
        
        return images
    
    def detect_rotated_color(self, board):
        """
        Detecteer welke kleur rechts staat (na 90° rotatie = rijen 6,7,8)
        en stel deze in als rotated_color
        
        Args:
            board: python-chess Board object
        """
        # Rijen 6,7,8 komen na rotatie rechts te staan
        white_count = 0
        black_count = 0
        
        for row_num in [6, 7, 8]:
            for col in range(8):
                square = chess.square(col, row_num - 1)  # 0-indexed
                piece = board.piece_at(square)
                if piece:
                    if piece.color:  # True = white
                        white_count += 1
                    else:  # False = black
                        black_count += 1
        
        # Stel rotated_color in
        if white_count > black_count:
            self.rotated_color = True  # White
            print(f"Chess: Detected white on right side - will rotate white pieces 180°")
        elif black_count > white_count:
            self.rotated_color = False  # Black
            print(f"Chess: Detected black on right side - will rotate black pieces 180°")
        else:
            self.rotated_color = None
            print(f"Chess: No clear color on right - no rotation")
    
    def _get_square_notation(self, row, col):
        """Converteer row/col naar chess notatie (A1-H8)"""
        return f"{chr(65 + col)}{8 - row}"
    
    def draw_pieces(self, board):
        """
        Teken chess pieces met PNG images
        
        Args:
            board: python-chess Board object
        """
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = board.piece_at(square)
                
                if piece:
                    # Haal image op
                    image = self.piece_images[piece.symbol()]
                    
                    # Roteer pieces van de kleur die rechts staat 180 graden
                    if self.rotated_color is not None and piece.color == self.rotated_color:
                        image = pygame.transform.rotate(image, 180)
                    
                    # Center image in square
                    image_rect = image.get_rect(
                        center=(
                            col * self.square_size + self.square_size // 2,
                            row * self.square_size + self.square_size // 2
                        )
                    )
                    self.screen.blit(image, image_rect)
    
    def get_square_from_pos(self, pos):
        """
        Converteer muis positie naar chess square notatie
        
        Args:
            pos: (x, y) tuple van muis positie
            
        Returns:
            String zoals "E2" of None als niet op bord geklikt
        """
        x, y = pos
        
        # Check of klik binnen bord is
        if x < 0 or x >= self.board_size or y < 0 or y >= self.board_size:
            return None
        
        # Converteer naar kolom en rij
        col = x // self.square_size
        row = 7 - (y // self.square_size)  # Flip voor chess coördinaten
        
        # Converteer naar chess notatie
        files = 'ABCDEFGH'
        return f"{files[col]}{row + 1}"
