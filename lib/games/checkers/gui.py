#!/usr/bin/env python3
"""
Checkers GUI met Pygame

GUI voor damspel (American Checkers / English Draughts).
Hergebruikt veel van de chess GUI infrastructuur.

Functionaliteit:
- Rendering van 8x8 dambord (alleen donkere vakken actief)
- Display van checkers pieces (men en kings)
- Hergebruikt dialogs, sidebar, event handlers van chess
- Piece selection en move highlighting

Verschillen met Chess:
- Alleen donkere vakken zijn actief
- 4 piece types: white man, white king, black man, black king
- Andere piece images (assets/checkers_pieces/)

Architectuur:
- Gebruikt bestaande DialogRenderer, SidebarRenderer, EventHandlers
- Eigen BoardRenderer voor checkers-specifiek bord
- Eigen piece loading voor checkers images
"""

import pygame
import os
from lib.games.checkers.engine import CheckersEngine
from lib.settings import Settings
from lib.gui.widgets import UIWidgets
from lib.gui.dialogs import DialogRenderer
from lib.gui.settings_dialog import SettingsDialog
from lib.games.checkers.board import CheckersBoardRenderer
from lib.games.checkers.sidebar import CheckersSidebarRenderer
from lib.games.checkers.settings_dialog import CheckersSettingsTabs
from lib.gui.event_handlers import EventHandlers


class CheckersGUI:
    """Pygame GUI voor checkers bord visualisatie"""
    
    # Kleuren (checkers gebruikt traditioneel groen/beige bord)
    COLOR_LIGHT_SQUARE = (240, 217, 181)  # Beige (niet-speelbaar)
    COLOR_DARK_SQUARE = (60, 120, 60)     # Donkergroen (speelbaar)
    COLOR_HIGHLIGHT = (186, 202, 68)      # Geel voor legal moves
    COLOR_SELECTION = (255, 215, 0)       # Goud voor geselecteerd veld
    COLOR_BG = (50, 50, 50)
    COLOR_SIDEBAR = (240, 240, 240)
    COLOR_WHITE = (255, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    COLOR_BUTTON = (70, 130, 180)
    COLOR_BUTTON_HOVER = (100, 149, 237)
    
    def __init__(self, engine):
        """
        Initialiseer GUI
        
        Args:
            engine: CheckersEngine instance
        """
        pygame.init()
        
        self.engine = engine
        self.settings = Settings()
        
        # Fullscreen setup (hergebruikt van chess)
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        self.board_size = self.screen_height
        self.sidebar_width = self.screen_width - self.board_size
        
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height),
            pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
        )
        pygame.display.set_caption("Checkers Board")
        
        # Board parameters
        self.square_size = self.board_size // 8
        
        # Fonts
        self.font = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 48)
        
        # Buttons (hergebruikt layout van chess)
        button_width = 125
        button_height = 55
        button_spacing = 10
        
        total_button_width = 2 * button_width + button_spacing
        button_start_x = self.board_size + (self.sidebar_width - total_button_width) // 2
        
        self.new_game_button = pygame.Rect(
            button_start_x,
            self.screen_height - 130,
            button_width,
            button_height
        )
        
        self.exit_button = pygame.Rect(
            button_start_x + button_width + button_spacing,
            self.screen_height - 130,
            button_width,
            button_height
        )
        
        self.settings_button = pygame.Rect(
            button_start_x,
            self.screen_height - 130 + button_height + button_spacing,
            button_width,
            button_height
        )
        
        # State
        self.show_settings = False
        self.show_exit_confirm = False
        self.show_new_game_confirm = False
        self.show_power_dropdown = False
        self.highlighted_squares = {'destinations': [], 'intermediate': []}
        self.selected_piece = None
        self.selected_piece_from = None
        self.active_settings_tab = 'general'
        self.active_sensor_states = {}
        self.dragging_slider = False  # Voor brightness slider drag
        self.dragging_stockfish_slider = False  # Voor AI skill slider (toekomstig gebruik)
        
        # Renderers (hergebruik van chess GUI infrastructure)
        self.board_renderer = CheckersBoardRenderer(
            self.screen,
            self.board_size,
            self.square_size,
            self.font_small
        )
        
        self.dialog_renderer = DialogRenderer(
            self.screen,
            self.screen_width,
            self.screen_height,
            self.font,
            self.font_small
        )
        
        self.sidebar_renderer = CheckersSidebarRenderer(
            self.screen,
            self.board_size,
            self.sidebar_width,
            self.screen_height,
            self.font,
            self.font_small,
            self.board_renderer.piece_images  # Pass checkers pieces from board renderer
        )
        
        self.settings_dialog = SettingsDialog(
            self.screen,
            self.screen_width,
            self.screen_height,
            self.font,
            self.font_small,
            self
        )
        
        self.events = EventHandlers(self)
        
        # Temp settings storage
        self.temp_settings = {}
    
    def draw_board(self):
        """Teken checkers bord"""
        # Voeg selected square toe aan highlights voor gouden outline
        if isinstance(self.highlighted_squares, dict):
            highlights = self.highlighted_squares.copy()
            if self.selected_piece_from:
                # Voeg selected square toe aan destinations
                if self.selected_piece_from not in highlights['destinations']:
                    highlights['destinations'] = highlights['destinations'] + [self.selected_piece_from]
        else:
            # Fallback voor backwards compatibility
            highlights = self.highlighted_squares.copy()
            if self.selected_piece_from:
                highlights.append(self.selected_piece_from)
        
        self.board_renderer.draw_board(highlighted_squares=highlights)
    
    def draw_coordinates(self):
        """Teken coordinaten"""
        if self.settings.get('show_coordinates', True, section='debug'):
            self.board_renderer.draw_coordinates()
    
    def draw_pieces(self):
        """Teken checkers pieces"""
        # Converteer engine board naar format voor BoardRenderer
        board_state = {}
        for row in range(8):
            for col in range(8):
                chess_pos = f"{chr(65 + col).lower()}{8 - row}"
                piece = self.engine.get_piece_at(chess_pos.upper())
                
                if piece:
                    piece_type = f"{piece.color}_{'king' if piece.is_king else 'man'}"
                    board_state[chess_pos] = piece_type
        
        self.board_renderer.draw_pieces(board_state)
    
    def draw_debug_overlays(self):
        """Teken debug overlays"""
        if self.settings.get('debug_sensors', False, section='debug'):
            self.board_renderer.draw_debug_overlays(self.active_sensor_states)
    
    def draw_sidebar(self):
        """Teken sidebar (hergebruikt SidebarRenderer)"""
        self.sidebar_renderer.draw_sidebar(
            self.engine,
            self.new_game_button,
            self.exit_button,
            self.settings_button
        )
    
    def draw_settings_dialog(self):
        """Teken settings dialog met checkers-specifieke tabs (Gameplay + AI)"""
        # Gebruik temp_settings als die bestaat, anders echte settings
        active_settings = self.temp_settings if self.temp_settings else self.settings.settings
        
        # Checkers-specifieke tabs (AI tab enabled als vs_computer aan staat)
        vs_computer = active_settings.get('checkers', {}).get('play_vs_computer', False)
        custom_tabs = [
            ('gameplay_checkers', 'Gameplay', True),
            ('ai_checkers', 'AI', vs_computer)  # Grayed out als vs_computer uit staat
        ]
        
        # Checkers-specifieke renderers (wrapper lambdas om screen + font_small door te geven)
        custom_renderers = {
            'gameplay_checkers': lambda dx, cy, s, r: CheckersSettingsTabs.render_gameplay_tab(
                self.screen, self.font_small, dx, cy, s, r
            ),
            'ai_checkers': lambda dx, cy, s, r: CheckersSettingsTabs.render_ai_tab(
                self.screen, self.font_small, dx, cy, s, r
            )
        }
        
        return self.settings_dialog.draw(
            active_settings,
            self.active_settings_tab,
            custom_tabs=custom_tabs,
            custom_renderers=custom_renderers
        )
    
    def draw(self, temp_message=None, temp_message_timer=0):
        """
        Main draw method
        
        Returns:
            Dict met UI components voor event handling
        """
        self.screen.fill(self.COLOR_BG)
        
        # Teken bord
        self.draw_board()
        
        # Teken pieces
        self.draw_pieces()
        
        # Teken debug overlays
        self.draw_debug_overlays()
        
        # Teken coordinaten
        if self.settings.get('show_coordinates', True):
            self.draw_coordinates()
        
        # Teken sidebar
        self.draw_sidebar()
        
        # Dialogs
        result = {}
        
        if self.show_exit_confirm:
            exit_yes_button, exit_no_button = self.dialog_renderer.draw_exit_confirm_dialog()
            result['exit_yes'] = exit_yes_button
            result['exit_no'] = exit_no_button
        elif self.show_new_game_confirm:
            new_game_yes_button, new_game_no_button = self.dialog_renderer.draw_new_game_confirm_dialog()
            result['new_game_yes'] = new_game_yes_button
            result['new_game_no'] = new_game_no_button
        elif self.show_settings:
            settings_result = self.draw_settings_dialog()
            result.update(settings_result)
            
            # Extract dropdown data
            dropdowns = settings_result.get('dropdowns', {})
            dropdown_items = settings_result.get('dropdown_items', [])
            power_profiles = settings_result.get('power_profiles', [])
            
            result['dropdowns'] = dropdowns
            result['dropdown_items'] = dropdown_items
            result['power_profiles'] = power_profiles
        
        # Temp message overlay - alleen als GEEN dialogs open zijn
        if temp_message and pygame.time.get_ticks() < temp_message_timer:
            if not (self.show_settings or self.show_exit_confirm or self.show_new_game_confirm):
                # Kies notification type op basis van message content
                if 'mismatch' in temp_message.lower() or 'invalid' in temp_message.lower():
                    UIWidgets.draw_notification(self.screen, temp_message, board_width=self.board_size, board_height=self.board_size, notification_type='error')
                else:
                    UIWidgets.draw_notification(self.screen, temp_message, board_width=self.board_size, board_height=self.board_size, notification_type='warning')
        
        pygame.display.flip()
        return result
    
    def highlight_squares(self, squares):
        """Set highlighted squares (dict met 'destinations' en 'intermediate' keys of list)"""
        if isinstance(squares, dict):
            self.highlighted_squares = squares
        else:
            # Backwards compatible: list wordt destinations
            self.highlighted_squares = {'destinations': squares if isinstance(squares, list) else [], 'intermediate': []}
    
    def set_selected_piece(self, piece, from_square):
        """Set selected piece"""
        self.selected_piece = piece
        self.selected_piece_from = from_square
    
    def update_sensor_debug_states(self, sensor_states):
        """Update sensor debug visualisatie"""
        self.active_sensor_states = sensor_states
    
    def get_square_from_pos(self, pos):
        """Converteer mouse pos naar chess notatie (delegates to BoardRenderer)"""
        return self.board_renderer.get_square_from_pos(pos)
    
    # Event handler delegations
    def handle_new_game_click(self, pos):
        """Handle klik op new game button"""
        if self.new_game_button.collidepoint(pos):
            self.show_new_game_confirm = True
            return True
        return False
    
    def handle_exit_click(self, pos):
        """Handle klik op exit button"""
        if self.exit_button.collidepoint(pos):
            self.show_exit_confirm = True
            return True
        return False
    
    def handle_settings_click(self, pos):
        """Handle klik op settings button"""
        if self.settings_button.collidepoint(pos):
            self.show_settings = True
            self.temp_settings = self.settings.settings.copy()
            return True
        return False
    
    def handle_ok_click(self, pos, ok_button):
        """Handle klik op OK in settings"""
        return self.events.handle_ok_click(pos, ok_button)
    
    def handle_exit_yes_click(self, pos, button):
        """Handle klik op Yes in exit confirmation"""
        if button and button.collidepoint(pos):
            return True
        return False
    
    def handle_exit_no_click(self, pos, button):
        """Handle klik op No in exit confirmation"""
        if button and button.collidepoint(pos):
            self.show_exit_confirm = False
            return True
        return False
    
    def handle_new_game_yes_click(self, pos, button):
        """Handle klik op Yes in new game confirmation"""
        if button and button.collidepoint(pos):
            return True
        return False
    
    def handle_new_game_no_click(self, pos, button):
        """Handle klik op No in new game confirmation"""
        if button and button.collidepoint(pos):
            self.show_new_game_confirm = False
            return True
        return False
    
    def quit(self):
        """Cleanup pygame"""
        pygame.quit()
