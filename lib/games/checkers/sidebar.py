#!/usr/bin/env python3
"""
Checkers Sidebar Renderer

Checkers-specifieke sidebar met captured pieces count
"""

import pygame
from collections import Counter
from lib.gui.sidebar import BaseSidebarRenderer


class CheckersSidebarRenderer(BaseSidebarRenderer):
    """Renders checkers-specific sidebar"""
    
    def __init__(self, screen, board_size, sidebar_width, screen_height, font, font_small, piece_images):
        super().__init__(screen, board_size, sidebar_width, screen_height, font, font_small)
        self.piece_images = piece_images
    
    def draw_sidebar(self, engine, new_game_button, exit_button, settings_button, undo_button, game_started=False, update_available=False, update_version_info=""):
        """Teken checkers sidebar"""
        # Background
        self.draw_background()
        
        y_offset = 30
        
        # Turn + Move op 1 regel (zelfde als chess)
        current_turn = engine.whose_turn().capitalize()
        move_num = engine.get_move_number()
        game_info = f"Turn: {current_turn}  |  Move: {move_num}"
        info_text = self.font.render(game_info, True, (60, 60, 60))
        info_rect = info_text.get_rect(center=(self.board_size + self.sidebar_width // 2, y_offset))
        self.screen.blit(info_text, info_rect)
        y_offset += 50
        
        # Game status
        if engine.is_game_over():
            result = engine.get_game_result()
            status = self.font_small.render(result, True, (255, 0, 0))
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
        
        # Captured pieces (zelfde stijl als chess)
        captured = engine.get_captured_pieces()
        
        # White captured (black pieces)
        cap_label = self.font_small.render("Captured by White:", True, self.COLOR_BLACK)
        self.screen.blit(cap_label, (self.board_size + 20, y_offset))
        y_offset += 30
        
        x_pos = self.board_size + 20
        y_offset = self._draw_captured_with_counts(captured['white'], 'black', x_pos, y_offset)
        
        # Black captured (white pieces)
        cap_label = self.font_small.render("Captured by Black:", True, self.COLOR_BLACK)
        self.screen.blit(cap_label, (self.board_size + 20, y_offset))
        y_offset += 30
        
        x_pos = self.board_size + 20
        y_offset = self._draw_captured_with_counts(captured['black'], 'white', x_pos, y_offset)
        
        # Update notification (boven buttons)
        update_rect = self.draw_update_notification(update_available, update_version_info)
        
        # Buttons
        # Check of er zetten zijn om ongedaan te maken (move_count > 0)
        can_undo = engine.move_count > 0
        self.draw_buttons(new_game_button, exit_button, settings_button, undo_button, game_started=game_started, can_undo=can_undo)
        
        return update_rect
    
    def _draw_captured_with_counts(self, pieces, piece_color, x_start, y_start):
        """Teken captured pieces met count nummers (zelfde als chess)"""
        if not pieces:
            return y_start + 35
        
        # Tel pieces (in checkers is het simpel - alleen men en kings)
        piece_count = Counter(pieces)
        
        # Teken pieces met counts (eerst kings, dan men)
        piece_types = ['king', 'man']
        x_pos = x_start
        
        for piece_type in piece_types:
            count = piece_count.get(piece_type, 0)
            if count == 0:
                continue
            
            # Haal juiste image op
            piece_key = f"{piece_color}_{piece_type}"
            piece_img = self.piece_images.get(piece_key)
            
            if piece_img:
                small_img = pygame.transform.smoothscale(piece_img, (30, 30))
                self.screen.blit(small_img, (x_pos, y_start))
                
                # Toon count als > 1 (zelfde stijl als chess)
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

        self.draw_buttons(new_game_button, exit_button, settings_button)
