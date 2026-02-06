#!/usr/bin/env python3
"""
Chess Sidebar Renderer

Chess-specifieke sidebar met check/checkmate status en captured pieces
"""

import pygame
import chess
from collections import Counter
from lib.gui.sidebar import BaseSidebarRenderer


class ChessSidebarRenderer(BaseSidebarRenderer):
    """Renders chess-specific sidebar"""
    
    def __init__(self, screen, board_size, sidebar_width, screen_height, font, font_small, piece_images):
        super().__init__(screen, board_size, sidebar_width, screen_height, font, font_small)
        self.piece_images = piece_images
    
    def draw_sidebar(self, engine, new_game_button, exit_button, settings_button):
        """Teken chess sidebar"""
        # Background
        self.draw_background()
        
        y_offset = 30
        
        # Turn + Move op 1 regel
        current_turn = "White" if engine.board.turn == chess.WHITE else "Black"
        move_num = engine.get_move_number()
        game_info = f"Turn: {current_turn}  |  Move: {move_num}"
        info_text = self.font.render(game_info, True, (60, 60, 60))
        info_rect = info_text.get_rect(center=(self.board_size + self.sidebar_width // 2, y_offset))
        self.screen.blit(info_text, info_rect)
        y_offset += 50
        
        # Game status
        if engine.is_checkmate():
            status = self.font_small.render("CHECKMATE!", True, (255, 0, 0))
            self.screen.blit(status, (self.board_size + 20, y_offset))
            y_offset += 30
        elif engine.is_in_check():
            status = self.font_small.render("CHECK!", True, (255, 100, 0))
            self.screen.blit(status, (self.board_size + 20, y_offset))
            y_offset += 30
        elif engine.is_stalemate():
            status = self.font_small.render("STALEMATE", True, (100, 100, 100))
            self.screen.blit(status, (self.board_size + 20, y_offset))
            y_offset += 30
        
        # Last move
        last_move = engine.get_last_move()
        if last_move:
            move_label = self.font_small.render("Last move:", True, self.COLOR_BLACK)
            self.screen.blit(move_label, (self.board_size + 20, y_offset))
            move_value = self.font_small.render(str(last_move), True, self.COLOR_BLACK)
            self.screen.blit(move_value, (self.board_size + 20, y_offset + 25))
            y_offset += 60
        
        # Captured pieces
        captured = engine.get_captured_pieces()
        
        # White captured (black pieces)
        cap_label = self.font_small.render("Captured by White:", True, self.COLOR_BLACK)
        self.screen.blit(cap_label, (self.board_size + 20, y_offset))
        y_offset += 30
        
        x_pos = self.board_size + 20
        y_offset = self._draw_captured_with_counts(captured['black'], x_pos, y_offset)
        
        # Black captured (white pieces)
        cap_label = self.font_small.render("Captured by Black:", True, self.COLOR_BLACK)
        self.screen.blit(cap_label, (self.board_size + 20, y_offset))
        y_offset += 30
        
        x_pos = self.board_size + 20
        y_offset = self._draw_captured_with_counts(captured['white'], x_pos, y_offset)
        
        # Buttons
        self.draw_buttons(new_game_button, exit_button, settings_button)
    
    def _draw_captured_with_counts(self, pieces, x_start, y_start):
        """Teken captured pieces met count nummers"""
        if not pieces:
            return y_start + 35
        
        # Groepeer en tel stukken
        piece_counts = Counter(pieces)
        
        # Teken pieces met counts
        piece_types = ['q', 'Q', 'r', 'R', 'b', 'B', 'n', 'N', 'p', 'P']
        x_pos = x_start
        
        for piece_type in piece_types:
            count = piece_counts.get(piece_type, 0)
            if count == 0:
                continue
                
            piece_img = self.piece_images.get(piece_type.lower() if piece_type.islower() else piece_type.upper())
            if piece_img:
                small_img = pygame.transform.smoothscale(piece_img, (30, 30))
                self.screen.blit(small_img, (x_pos, y_start))
                
                # Toon count als > 1
                if count > 1:
                    count_text = f"{count}x"
                    
                    # Zwarte outline
                    for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]:
                        outline = self.font_small.render(count_text, True, self.COLOR_BLACK)
                        self.screen.blit(outline, (x_pos + 10 + dx, y_start - 5 + dy))
                    
                    # Witte tekst
                    count_surface = self.font_small.render(count_text, True, self.COLOR_WHITE)
                    self.screen.blit(count_surface, (x_pos + 10, y_start - 5))
                
                x_pos += 35
                if x_pos > self.board_size + self.sidebar_width - 35:
                    x_pos = x_start
                    y_start += 35
        
        return y_start + 40

