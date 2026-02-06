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
    
    def _get_square_notation(self, row, col):
        """Converteer row/col naar chess notatie (A1-H8)"""
        return f"{chr(65 + col)}{8 - row}"
    
    def draw_coordinates(self):
        """Teken chess coördinaten (A-H, 1-8)"""
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
