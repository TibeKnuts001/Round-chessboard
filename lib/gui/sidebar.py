#!/usr/bin/env python3
"""
Sidebar Rendering Module

Toont game informatie en control buttons rechts van het schaakbord.
Biedt real-time game state feedback en interactieve controls.

Weergegeven informatie:
- Current turn indicator ("White to move" / "Black to move")
- Game state (Check!, Checkmate!, Stalemate!, Draw!)
- Captured pieces per kleur met material count
- Move counter (aantal halve zetten)

Buttons:
- New Game: Start nieuw spel (vraagt confirmatie)
- Settings: Open settings dialog
- Quit: Sluit applicatie af (vraagt confirmatie)

Layout:
- Breedte: 200 pixels
- Positie: Rechts van 640px bord (x=640)
- Background: Lichtgrijs (220, 220, 220)
- Button spacing: 20px tussen buttons

Visuele feedback:
- Active turn highlighted in blauw
- Check state shown in rood met uitroepteken
- Captured pieces met SVG sprites (48x48)
- Material advantage: +2, -1 etc naast captured pieces

Hoofdklasse:
- SidebarRenderer: Static methods voor sidebar components

Wordt gebruikt door: ChessGUI.draw()
"""

import pygame
import chess
from collections import Counter


class SidebarRenderer:
    """Tekent de sidebar met game informatie"""
    
    # Kleuren
    COLOR_SIDEBAR = (240, 240, 240)  # Licht grijs
    COLOR_WHITE = (255, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    COLOR_BUTTON = (70, 130, 180)
    COLOR_BUTTON_HOVER = (100, 149, 237)
    
    def __init__(self, screen, board_size, sidebar_width, screen_height, font, font_small, piece_images):
        """
        Args:
            screen: Pygame screen surface
            board_size: Grootte van het bord in pixels
            sidebar_width: Breedte van sidebar
            screen_height: Hoogte van scherm
            font: Main font
            font_small: Small font
            piece_images: Dict met piece images (van BoardRenderer)
        """
        self.screen = screen
        self.board_size = board_size
        self.sidebar_width = sidebar_width
        self.screen_height = screen_height
        self.font = font
        self.font_small = font_small
        self.piece_images = piece_images
    
    def draw_sidebar(self, engine, new_game_button, exit_button, settings_button):
        """
        Teken sidebar met turn indicator, stats, en buttons
        
        Args:
            engine: ChessEngine instance
            new_game_button: pygame.Rect voor new game button
            exit_button: pygame.Rect voor exit button
            settings_button: pygame.Rect voor settings button
        """
        # Achtergrond sidebar (licht grijs)
        sidebar_rect = pygame.Rect(self.board_size, 0, self.sidebar_width, self.screen_height)
        pygame.draw.rect(self.screen, self.COLOR_SIDEBAR, sidebar_rect)
        
        # Verticale scheidingslijn tussen bord en sidebar (subtiel)
        separator_color = (160, 140, 110)  # Donkerder beige
        pygame.draw.line(
            self.screen,
            separator_color,
            (self.board_size, 0),
            (self.board_size, self.screen_height),
            3  # 3px breed
        )
        
        sidebar_x = self.board_size + self.sidebar_width // 2
        y_pos = 30
        
        # 1. Turn + Move op 1 regel
        current_turn = "White" if engine.board.turn == chess.WHITE else "Black"
        move_num = engine.get_move_number()
        
        game_info = f"Turn: {current_turn}  |  Move: {move_num}"
        info_text = self.font.render(game_info, True, (60, 60, 60))
        info_rect = info_text.get_rect(center=(sidebar_x, y_pos))
        self.screen.blit(info_text, info_rect)
        
        y_pos += 50
        
        # 2. Check indicator + Checkmate/Stalemate
        if engine.is_checkmate():
            checkmate_text = self.font.render("CHECKMATE!", True, (200, 0, 0))
            checkmate_rect = checkmate_text.get_rect(center=(sidebar_x, y_pos))
            self.screen.blit(checkmate_text, checkmate_rect)
            y_pos += 30
            
            # Winner indicator
            winner = "White" if engine.get_board().turn == chess.BLACK else "Black"
            winner_text = self.font_small.render(f"{winner} wins!", True, (0, 150, 0))
            winner_rect = winner_text.get_rect(center=(sidebar_x, y_pos))
            self.screen.blit(winner_text, winner_rect)
            y_pos += 40
        elif engine.is_stalemate():
            stalemate_text = self.font.render("STALEMATE!", True, (150, 150, 0))
            stalemate_rect = stalemate_text.get_rect(center=(sidebar_x, y_pos))
            self.screen.blit(stalemate_text, stalemate_rect)
            y_pos += 30
            
            draw_text = self.font_small.render("Draw!", True, (100, 100, 100))
            draw_rect = draw_text.get_rect(center=(sidebar_x, y_pos))
            self.screen.blit(draw_text, draw_rect)
            y_pos += 40
        elif engine.is_in_check():
            check_text = self.font.render("CHECK!", True, (220, 50, 50))
            check_rect = check_text.get_rect(center=(sidebar_x, y_pos))
            self.screen.blit(check_text, check_rect)
            y_pos += 40
        
        # 3. Last move
        last_move = engine.get_last_move()
        if last_move:
            last_move_label = self.font_small.render("Last move:", True, (100, 100, 100))
            last_move_rect = last_move_label.get_rect(center=(sidebar_x, y_pos))
            self.screen.blit(last_move_label, last_move_rect)
            
            last_move_text = self.font.render(last_move, True, (60, 60, 60))
            last_move_text_rect = last_move_text.get_rect(center=(sidebar_x, y_pos + 30))
            self.screen.blit(last_move_text, last_move_text_rect)
            
            y_pos += 70
        
        # 4. Captured pieces
        captured = engine.get_captured_pieces()
        
        # White captured (by black)
        y_pos += 10
        y_pos = self._draw_captured_section(captured['white'], "White lost:", y_pos, sidebar_x)
        
        # Black captured (by white)
        y_pos += 10
        y_pos = self._draw_captured_section(captured['black'], "Black lost:", y_pos, sidebar_x)
        
        # 5. Buttons grid (2x2) onderaan
        mouse_pos = pygame.mouse.get_pos()
        
        # Eerste rij: New Game + Exit
        new_game_color = (50, 150, 50) if new_game_button.collidepoint(mouse_pos) else (70, 180, 70)
        pygame.draw.rect(self.screen, new_game_color, new_game_button, border_radius=10)
        new_game_text = self.font_small.render("New Game", True, self.COLOR_WHITE)
        new_game_text_rect = new_game_text.get_rect(center=new_game_button.center)
        self.screen.blit(new_game_text, new_game_text_rect)
        
        exit_color = (200, 50, 50) if exit_button.collidepoint(mouse_pos) else (180, 70, 70)
        pygame.draw.rect(self.screen, exit_color, exit_button, border_radius=10)
        exit_text = self.font_small.render("Exit", True, self.COLOR_WHITE)
        exit_text_rect = exit_text.get_rect(center=exit_button.center)
        self.screen.blit(exit_text, exit_text_rect)
        
        # Tweede rij: Settings + placeholder
        settings_color = self.COLOR_BUTTON_HOVER if settings_button.collidepoint(mouse_pos) else self.COLOR_BUTTON
        pygame.draw.rect(self.screen, settings_color, settings_button, border_radius=10)
        settings_text = self.font_small.render("Settings", True, self.COLOR_WHITE)
        settings_text_rect = settings_text.get_rect(center=settings_button.center)
        self.screen.blit(settings_text, settings_text_rect)
    
    def _draw_captured_section(self, pieces, label_text, y_start, sidebar_x):
        """
        Teken captured pieces sectie
        
        Args:
            pieces: List van piece symbols
            label_text: Label tekst
            y_start: Y positie om te starten
            sidebar_x: X center van sidebar
            
        Returns:
            Nieuwe y positie
        """
        # Toon label altijd
        label = self.font_small.render(label_text, True, (100, 100, 100))
        label_rect = label.get_rect(center=(sidebar_x, y_start))
        self.screen.blit(label, label_rect)
        y_start += 30
        
        if not pieces:
            # Toon "-" als er niets gepakt is
            none_text = self.font_small.render("-", True, (150, 150, 150))
            none_rect = none_text.get_rect(center=(sidebar_x, y_start))
            self.screen.blit(none_text, none_rect)
            return y_start + 35
        
        # Groepeer en tel stukken
        piece_counts = Counter(pieces)
        
        # Teken pieces met counts
        piece_types = ['q', 'Q', 'r', 'R', 'b', 'B', 'n', 'N', 'p', 'P']
        pieces_to_draw = [(p, count) for p in piece_types for count in [piece_counts.get(p, 0)] if count > 0]
        
        x_offset = sidebar_x - (len(pieces_to_draw) * 20)
        for piece_symbol, count in pieces_to_draw:
            if piece_symbol in self.piece_images:
                small_size = 35
                small_image = pygame.transform.smoothscale(
                    self.piece_images[piece_symbol],
                    (small_size, small_size)
                )
                self.screen.blit(small_image, (x_offset, y_start))
                
                # Toon count als > 1
                if count > 1:
                    count_text = f"{count}x"
                    
                    # Teken zwarte outline
                    for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]:
                        outline = self.font_small.render(count_text, True, self.COLOR_BLACK)
                        self.screen.blit(outline, (x_offset + 10 + dx, y_start - 5 + dy))
                    
                    # Teken witte tekst
                    count_surface = self.font_small.render(count_text, True, self.COLOR_WHITE)
                    self.screen.blit(count_surface, (x_offset + 10, y_start - 5))
                
                x_offset += 40
        
        return y_start + 50
