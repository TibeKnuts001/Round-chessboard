#!/usr/bin/env python3
"""
Board Rendering Module

Handelt alle visuele weergave van het schaakbord:
velden, stukken, coördinaten, highlights en debug overlays.

Functionaliteit:
- 8x8 schaakbord rendering met afwisselende kleuren
- Chess piece rendering via SVG sprites (64x64 pixels)
- Coordinate labels (A-H horizontaal, 1-8 verticaal)
- Selected piece highlighting (gele border)
- Drag-and-drop visualization (stuk volgt muis)
- Debug mode: sensor detection overlay (rood/groen vakken)

Assets:
- Piece sprites: assets/pieces/*.svg (12 files voor elke stuk/kleur)
- Layout: 640x640 pixel board (80x80 per veld)

Visuele feedback:
- Light squares: (240, 217, 181) beige
- Dark squares: (181, 136, 99) bruin  
- Selected: gele 4px border
- Debug occupied: rood overlay (sensor triggered)
- Debug empty: groen overlay (no sensor signal)

Hoofdklasse:
- BoardRenderer: Static drawing methods voor board components

Wordt gebruikt door: ChessGUI.draw()
"""

import os
import pygame
import chess


class BoardRenderer:
    """Tekent het schaakbord en pieces"""
    
    # Kleuren
    COLOR_LIGHT_SQUARE = (240, 217, 181)
    COLOR_DARK_SQUARE = (181, 136, 99)
    COLOR_HIGHLIGHT = (186, 202, 68)
    COLOR_SELECTION = (255, 215, 0)  # Goud voor geselecteerd veld
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
        self.font = pygame.font.Font(None, 36)  # Voor debug overlays
        
        # Laad piece images
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
        # Navigate to assets from lib/gui/board.py
        assets_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
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
    
    def draw_board(self, highlighted_squares, selected_piece_from):
        """
        Teken schaakbord met highlights en selectie
        
        Args:
            highlighted_squares: List van chess notaties voor highlighted velden
            selected_piece_from: Chess notatie van geselecteerd veld of None
        """
        for row in range(8):
            for col in range(8):
                # Bepaal kleur
                is_light = (row + col) % 2 == 0
                color = self.COLOR_LIGHT_SQUARE if is_light else self.COLOR_DARK_SQUARE
                
                # Check of veld highlighted moet zijn
                chess_pos = f"{chr(65 + col)}{8 - row}"
                if chess_pos in highlighted_squares:
                    color = self.COLOR_HIGHLIGHT
                
                # Teken veld
                rect = pygame.Rect(
                    col * self.square_size,
                    row * self.square_size,
                    self.square_size,
                    self.square_size
                )
                pygame.draw.rect(self.screen, color, rect)
                
                # Teken selectie cirkel als dit het geselecteerde veld is (met knippereffect)
                if selected_piece_from and chess_pos == selected_piece_from:
                    # Bereken knipperstaat (500ms aan, 500ms uit)
                    blink_on = (pygame.time.get_ticks() // 500) % 2 == 0
                    
                    if blink_on:
                        center_x = col * self.square_size + self.square_size // 2
                        center_y = row * self.square_size + self.square_size // 2
                        radius = self.square_size // 2 - 5
                        # Teken dikke cirkel (meerdere cirkels voor dikte)
                        for i in range(5):
                            pygame.draw.circle(
                                self.screen,
                                self.COLOR_SELECTION,
                                (center_x, center_y),
                                radius - i,
                                1
                            )
    
    def draw_coordinates(self):
        """Teken coördinaten over de stukken heen met outline"""
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
        Teken schaakstukken met PNG images
        
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
    
    def draw_debug_overlays(self, active_sensor_states):
        """
        Teken debug overlays (boven de pieces)
        
        Args:
            active_sensor_states: Dict met chess notaties en sensor states
        """
        # Teken magneet indicators voor actieve sensors
        for row in range(8):
            for col in range(8):
                chess_pos = f"{chr(65 + col)}{8 - row}"
                
                if chess_pos in active_sensor_states and active_sensor_states[chess_pos]:
                    # Teken geel magneet symbool in midden van veld
                    center_x = col * self.square_size + self.square_size // 2
                    center_y = row * self.square_size + self.square_size // 2
                    
                    indicator_radius = 18
                    
                    # Gele cirkel als achtergrond
                    pygame.draw.circle(self.screen, (255, 215, 0), (center_x, center_y), indicator_radius)
                    pygame.draw.circle(self.screen, (200, 170, 0), (center_x, center_y), indicator_radius, 2)
                    
                    # Teken "M" voor magneet
                    magnet_text = self.font.render("M", True, self.COLOR_BLACK)
                    text_rect = magnet_text.get_rect(center=(center_x, center_y))
                    self.screen.blit(magnet_text, text_rect)
    
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
