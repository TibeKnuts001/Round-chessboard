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
        
        # Eerste rij - dynamisch:
        # - Voor game: New Game (volle breedte)
        # - Na game start: Stop Game + Undo (naast elkaar)
        full_button_width = total_button_width
        self.new_game_button = pygame.Rect(
            button_start_x,
            self.screen_height - 130,
            button_width,  # Altijd normale breedte (voor Stop Game)
            button_height
        )
        
        self.undo_button = pygame.Rect(
            button_start_x + button_width + button_spacing,
            self.screen_height - 130,
            button_width,
            button_height
        )
        
        # Tweede rij (Settings, Exit)
        self.settings_button = pygame.Rect(
            button_start_x,
            self.screen_height - 130 + button_height + button_spacing,
            button_width,
            button_height
        )
        
        self.exit_button = pygame.Rect(
            button_start_x + button_width + button_spacing,
            self.screen_height - 130 + button_height + button_spacing,
            button_width,
            button_height
        )
        
        # State
        self.show_settings = False
        self.show_exit_confirm = False
        self.show_new_game_confirm = False
        self.show_stop_game_confirm = False  # Voor stop game confirmation
        self.show_skip_setup_step_confirm = False  # Voor skip setup step confirmation
        self.show_undo_confirm = False  # Voor undo confirmation
        self.show_power_dropdown = False
        self.assisted_setup_mode = False
        self.assisted_setup_step = 0
        self.assisted_setup_waiting = False
        self.highlighted_squares = {'destinations': [], 'intermediate': []}
        self.last_move_from = None  # Voor highlighting van laatste zet
        self.last_move_to = None
        self.last_move_intermediate = []  # Tussenposities bij multi-captures
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
        
        # Cached board surface voor betere performance
        self.cached_board = None
        self.cached_pieces = None  # Cache voor pieces
        self.last_board_state = None  # Track board state changes
        
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
        """Teken checkers bord - gebruik cache voor betere performance"""
        # Cache static board grid + coordinaten (alleen eerste keer)
        if self.cached_board is None:
            self.cached_board = pygame.Surface((self.board_size, self.board_size))
            temp_screen = self.screen
            self.screen = self.cached_board
            self.board_renderer.screen = self.cached_board
            
            # Teken grid en coordinaten op cache (static, 1x)
            self.board_renderer.draw_board(highlighted_squares={'destinations': [], 'intermediate': []}, last_move=None)
            if self.settings.get('show_coordinates', True, section='debug'):
                self.board_renderer.draw_coordinates()
            
            self.screen = temp_screen
            self.board_renderer.screen = temp_screen
        
        # Blit cached board (1 blit ipv 64+)
        self.screen.blit(self.cached_board, (0, 0))
        
        # Teken highlights en last move bovenop
        if isinstance(self.highlighted_squares, dict):
            highlights = self.highlighted_squares.copy()
            if self.selected_piece_from:
                if self.selected_piece_from not in highlights['destinations']:
                    highlights['destinations'] = highlights['destinations'] + [self.selected_piece_from]
        else:
            highlights = self.highlighted_squares.copy()
            if self.selected_piece_from:
                highlights.append(self.selected_piece_from)
        
        last_move = None
        if self.last_move_from and self.last_move_to:
            last_move = (self.last_move_from, self.last_move_to, self.last_move_intermediate)
        
        # Teken alleen highlights/selection bovenop
        if highlights or last_move:
            self.board_renderer.draw_highlights(highlighted_squares=highlights, last_move=last_move)
    
    def draw_coordinates(self):
        """Teken coördinaten - nu in cached board, skip deze call"""
        pass  # Coordinaten zitten al in cached board
    
    def draw_pieces(self):
        """Teken checkers pieces - gebruik cache"""
        # Converteer engine board naar format voor BoardRenderer
        board_state = {}
        for row in range(8):
            for col in range(8):
                chess_pos = f"{chr(65 + col).lower()}{8 - row}"
                piece = self.engine.get_piece_at(chess_pos.upper())
                
                if piece:
                    piece_type = f"{piece.color}_{'king' if piece.is_king else 'man'}"
                    board_state[chess_pos] = piece_type
        
        # Check of board veranderd is
        board_state_key = str(sorted(board_state.items()))
        if self.last_board_state != board_state_key:
            # Board changed - maak nieuwe cache
            self.cached_pieces = pygame.Surface((self.board_size, self.board_size), pygame.SRCALPHA)
            temp_screen = self.screen
            self.screen = self.cached_pieces
            self.board_renderer.screen = self.cached_pieces
            
            self.board_renderer.draw_pieces(board_state)
            
            self.screen = temp_screen
            self.board_renderer.screen = temp_screen
            self.last_board_state = board_state_key
        
        # Blit cached pieces
        if self.cached_pieces:
            self.screen.blit(self.cached_pieces, (0, 0))
    
    def draw_debug_overlays(self):
        """Teken debug overlays"""
        if self.settings.get('debug_sensors', False, section='debug'):
            self.board_renderer.draw_debug_overlays(self.active_sensor_states)
    
    def draw_sidebar(self, game_started=False):
        """Teken sidebar (hergebruikt SidebarRenderer)"""
        self.sidebar_renderer.draw_sidebar(
            self.engine,
            self.new_game_button,
            self.exit_button,
            self.settings_button,
            self.undo_button,
            game_started=game_started
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
    
    def draw(self, temp_message=None, temp_message_timer=0, game_started=False):
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
        self.draw_sidebar(game_started=game_started)
        
        # Dialogs
        result = {}
        
        if self.show_exit_confirm:
            exit_yes_button, exit_no_button = self.dialog_renderer.draw_exit_confirm_dialog()
            result['exit_yes'] = exit_yes_button
            result['exit_no'] = exit_no_button
        elif self.show_stop_game_confirm:
            stop_game_yes_button, stop_game_no_button = self.dialog_renderer.draw_stop_game_confirm_dialog()
            result['stop_game_yes'] = stop_game_yes_button
            result['stop_game_no'] = stop_game_no_button
        elif self.show_new_game_confirm:
            new_game_normal_button, new_game_assisted_button, new_game_cancel_button = self.dialog_renderer.draw_new_game_confirm_dialog()
            result['new_game_normal'] = new_game_normal_button
            result['new_game_assisted'] = new_game_assisted_button
            result['new_game_cancel'] = new_game_cancel_button
        elif self.show_skip_setup_step_confirm:
            skip_setup_yes_button, skip_setup_no_button = self.dialog_renderer.draw_skip_setup_step_dialog()
            result['skip_setup_yes'] = skip_setup_yes_button
            result['skip_setup_no'] = skip_setup_no_button
        elif self.show_undo_confirm:
            undo_yes_button, undo_no_button = self.dialog_renderer.draw_undo_confirm_dialog()
            result['undo_yes'] = undo_yes_button
            result['undo_no'] = undo_no_button
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
            if not (self.show_settings or self.show_exit_confirm or self.show_new_game_confirm or self.show_stop_game_confirm or self.show_skip_setup_step_confirm or self.show_undo_confirm):
                # Kies notification type op basis van message content
                # Als message een list is, check de eerste regel
                check_text = temp_message[0] if isinstance(temp_message, list) else temp_message
                if 'mismatch' in check_text.lower() or 'invalid' in check_text.lower():
                    UIWidgets.draw_notification(self.screen, temp_message, board_width=self.board_size, board_height=self.board_size, notification_type='error')
                else:
                    UIWidgets.draw_notification(self.screen, temp_message, board_width=self.board_size, board_height=self.board_size, notification_type='warning')
        
        # Voeg undo_button toe aan result
        result['undo_button'] = self.undo_button
        
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
    
    def set_last_move(self, from_square, to_square, intermediate=None):
        """Set laatste zet voor highlighting (inclusief intermediate squares bij multi-captures)"""
        self.last_move_from = from_square
        self.last_move_to = to_square
        self.last_move_intermediate = intermediate if intermediate else []
    
    def update_sensor_debug_states(self, sensor_states):
        """Update sensor debug visualisatie"""
        self.active_sensor_states = sensor_states
    
    def get_square_from_pos(self, pos):
        """Converteer mouse pos naar chess notatie (delegates to BoardRenderer)"""
        return self.board_renderer.get_square_from_pos(pos)
    
    # Event handler delegations
    def handle_new_game_click(self, pos):
        """Handle klik op new game button (wordt Stop Game tijdens spel)"""
        if self.new_game_button.collidepoint(pos):
            # Check of spel al gestart is
            game_started = getattr(self._game_instance, 'game_started', False) if hasattr(self, '_game_instance') else False
            
            if game_started:
                # Toon stop game confirmation
                self.show_stop_game_confirm = True
            else:
                # Toon new game confirmation
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
    
    def handle_new_game_normal_click(self, pos, button):
        """Handle klik op Normal in new game confirmation"""
        if button and button.collidepoint(pos):
            self.assisted_setup_mode = False
            return True
        return False
    
    def handle_new_game_assisted_click(self, pos, button):
        """Handle klik op Assisted in new game confirmation"""
        if button and button.collidepoint(pos):
            self.assisted_setup_mode = True
            self.assisted_setup_step = 0
            self.assisted_setup_waiting = True
            return True
        return False
    
    def handle_new_game_cancel_click(self, pos, button):
        """Handle klik op Cancel in new game confirmation"""
        if button and button.collidepoint(pos):
            self.show_new_game_confirm = False
            return True
        return False
    
    def handle_stop_game_yes_click(self, pos, button):
        """Handle klik op Yes in stop game confirmation"""
        if button and button.collidepoint(pos):
            return True
        return False
    
    def handle_stop_game_no_click(self, pos, button):
        """Handle klik op No in stop game confirmation"""
        if button and button.collidepoint(pos):
            self.show_stop_game_confirm = False
            return True
        return False
    
    def handle_skip_setup_yes_click(self, pos, yes_button):
        """Handle klik op Skip in skip setup step confirmation"""
        if yes_button and yes_button.collidepoint(pos):
            self.show_skip_setup_step_confirm = False
            return True
        return False
    
    def handle_skip_setup_no_click(self, pos, no_button):
        """Handle klik op Wait in skip setup step confirmation"""
        if no_button and no_button.collidepoint(pos):
            self.show_skip_setup_step_confirm = False
            return True
        return False
    
    def quit(self):
        """Cleanup pygame"""
        pygame.quit()
