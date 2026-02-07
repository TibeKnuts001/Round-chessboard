#!/usr/bin/env python3
"""
Chess GUI met Pygame

De hoofdklasse voor de grafische interface van het schaakspel.
Coördineert alle visuele elementen en delegeert user input naar EventHandlers.

Functionaliteit:
- Rendering van schaakbord, stukken en sidebar
- Display van dialogs (settings, confirmations, warnings)
- Piece selection en drag-and-drop visualisatie
- Temp message systeem (warnings voor illegale zetten)
- Coördinatie tussen GUI submodules (board, sidebar, dialogs, event_handlers)

Hoofdklasse:
- ChessGUI: Central GUI manager met draw methods en state

Architectuur:
- Gebruikt BoardRenderer voor bordweergave
- Gebruikt SidebarRenderer voor game info
- Gebruikt EventHandlers voor alle user interactions
- Gebruikt SettingsDialog en DialogRenderer voor popups

Wordt gebruikt door: chessgame.py (main game loop)
"""

import pygame
import chess
from lib.games.chess.engine import ChessEngine
from lib.settings import Settings
from lib.gui.widgets import UIWidgets
from lib.gui.dialogs import DialogRenderer
from lib.gui.settings_dialog import SettingsDialog
from lib.games.chess.board import ChessBoardRenderer
from lib.games.chess.sidebar import ChessSidebarRenderer
from lib.games.chess.settings_dialog import ChessSettingsTabs
from lib.gui.event_handlers import EventHandlers


class ChessGUI:
    """Pygame GUI voor schaakbord visualisatie"""
    
    # Kleuren
    COLOR_LIGHT_SQUARE = (240, 217, 181)
    COLOR_DARK_SQUARE = (181, 136, 99)
    COLOR_HIGHLIGHT = (186, 202, 68)
    COLOR_SELECTION = (255, 215, 0)  # Goud voor geselecteerd veld
    COLOR_BG = (50, 50, 50)
    COLOR_SIDEBAR = (240, 240, 240)  # Licht grijs voor sidebar
    COLOR_WHITE = (255, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    COLOR_BUTTON = (70, 130, 180)
    COLOR_BUTTON_HOVER = (100, 149, 237)
    
    def __init__(self, engine):
        """
        Initialiseer GUI
        
        Args:
            engine: ChessEngine instance
        """
        pygame.init()
        
        self.engine = engine
        self.settings = Settings()  # Laad settings
        
        # Fullscreen setup
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        self.board_size = self.screen_height
        self.sidebar_width = self.screen_width - self.board_size
        
        # Maak fullscreen window zonder window manager decorations
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height),
            pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
        )
        pygame.display.set_caption("Chess Board")
        
        # Board parameters
        self.square_size = self.board_size // 8
        
        # Font
        self.font = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 48)
        
        # Buttons grid (2x2) onderaan sidebar
        button_width = 125
        button_height = 55
        button_spacing = 10
        
        # Centreer buttons in sidebar
        total_button_width = 2 * button_width + button_spacing
        button_start_x = self.board_size + (self.sidebar_width - total_button_width) // 2
        
        # Eerste rij (New Game - full width)
        full_button_width = total_button_width
        self.new_game_button = pygame.Rect(
            button_start_x,
            self.screen_height - 130,
            full_button_width,
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
        self.show_power_dropdown = False  # Power profile dropdown open/gesloten
        self.assisted_setup_mode = False  # Assisted setup actief
        self.assisted_setup_step = 0  # Huidige stap in assisted setup
        self.assisted_setup_waiting = False  # Wacht op gebruiker om door te gaan
        self.highlighted_squares = []  # Normale moves (groen)
        self.capture_squares = []  # Capture moves (rood)
        self.last_move_from = None  # Voor highlighting van laatste zet
        self.last_move_to = None
        self.dragging_slider = False
        self.dragging_stockfish_slider = False
        self.selected_piece = None  # Opgepakte stuk (chess.Piece object)
        self.selected_piece_from = None  # Van welk veld opgepakt (bijv "E2")
        self.active_settings_tab = 'general'  # Active tab in settings ('general' of 'debug')
        self.active_sensor_states = {}  # Voor debug visualisatie
        
        # Renderers voor verschillende GUI componenten
        self.board_renderer = ChessBoardRenderer(
            self.screen,
            self.board_size,
            self.square_size,
            self.font_small
        )
        
        # Cached board surface voor betere performance
        self.cached_board = None
        self.cached_pieces = None  # Cache voor pieces
        self.board_cache_dirty = True  # Flag om te weten wanneer opnieuw te cachen
        self.last_board_fen = None  # Track board state changes
        
        self.sidebar_renderer = ChessSidebarRenderer(
            self.screen,
            self.board_size,
            self.sidebar_width,
            self.screen_height,
            self.font,
            self.font_small,
            self.board_renderer.piece_images  # Hergebruik piece images
        )
        
        # Dialog renderer (voor confirmation dialogs)
        self.dialog_renderer = DialogRenderer(
            self.screen,
            self.screen_width,
            self.screen_height,
            self.font,
            self.font_small
        )
        
        # Settings dialog renderer
        self.settings_dialog = SettingsDialog(
            self.screen,
            self.screen_width,
            self.screen_height,
            self.font,
            self.font_small,
            self
        )
        
        # Event handlers (delegeer alle click/drag handling)
        self.events = EventHandlers(self)
    
    def draw_board(self):
        """Teken schaakbord - gebruik cache voor betere performance"""
        # Cache static board grid + coordinaten (alleen eerste keer)
        if self.cached_board is None:
            self.cached_board = pygame.Surface((self.board_size, self.board_size))
            temp_screen = self.screen
            self.screen = self.cached_board
            self.board_renderer.screen = self.cached_board
            
            # Teken grid en coordinaten op cache (static, 1x)
            self.board_renderer.draw_board_grid({}, None, set())
            self.board_renderer.draw_coordinates()
            
            self.screen = temp_screen
            self.board_renderer.screen = temp_screen
        
        # Blit cached board (1 blit ipv 64+)
        self.screen.blit(self.cached_board, (0, 0))
        
        # Teken highlights bovenop (alleen als nodig)
        if self.highlighted_squares or self.selected_piece_from or self.capture_squares:
            self.board_renderer.draw_highlights(self.highlighted_squares, self.selected_piece_from, self.capture_squares)
    
    def draw_coordinates(self):
        """Teken coördinaten - nu in cached board, skip deze call"""
        pass  # Coordinaten zitten al in cached board
    
    def draw_pieces(self):
        """Teken schaakstukken - gebruik cache"""
        current_board = self.engine.get_board()
        current_fen = current_board.fen()
        
        # Check of board veranderd is (move gedaan)
        if self.last_board_fen != current_fen:
            # Board changed - maak nieuwe cache
            self.cached_pieces = pygame.Surface((self.board_size, self.board_size), pygame.SRCALPHA)
            temp_screen = self.screen
            self.screen = self.cached_pieces
            self.board_renderer.screen = self.cached_pieces
            
            self.board_renderer.draw_pieces(current_board)
            
            self.screen = temp_screen
            self.board_renderer.screen = temp_screen
            self.last_board_fen = current_fen
        
        # Blit cached pieces (alleen als cache bestaat)
        if self.cached_pieces:
            self.screen.blit(self.cached_pieces, (0, 0))
    
    def draw_debug_overlays(self):
        """Teken debug overlays"""
        if self.settings.get('debug_sensors', False, section='debug'):
            self.board_renderer.draw_debug_overlays(self.active_sensor_states)
    
    def draw_sidebar(self):
        """Teken sidebar"""
        # Haal game_started op van de parent game instance (als die bestaat)
        game_started = False
        if hasattr(self, '_game_instance'):
            game_started = getattr(self._game_instance, 'game_started', False)
        
        self.sidebar_renderer.draw_sidebar(
            self.engine,
            self.new_game_button,
            self.exit_button,
            self.settings_button,
            game_started=game_started
        )
    
    def draw_settings_dialog(self):
        """Teken settings dialog met chess-specifieke tabs (Gameplay + AI)"""
        # Gebruik temp_settings als die bestaat, anders echte settings
        active_settings = self.temp_settings if self.temp_settings else self.settings
        
        # Chess-specifieke tabs (AI tab enabled als vs_computer aan staat)
        vs_computer = active_settings.get('chess', {}).get('play_vs_computer', False)
        custom_tabs = [
            ('gameplay', 'Gameplay', True),
            ('ai', 'AI', vs_computer)  # Grayed out als vs_computer uit staat
        ]
        
        # Chess-specifieke renderers (wrapper lambdas om screen + font_small door te geven)
        custom_renderers = {
            'gameplay': lambda dx, cy, s, r: ChessSettingsTabs.render_gameplay_tab(
                self.screen, self.font_small, dx, cy, s, r
            ),
            'ai': lambda dx, cy, s, r: ChessSettingsTabs.render_ai_tab(
                self.screen, self.font_small, dx, cy, s, r
            )
        }
        
        return self.settings_dialog.draw(
            active_settings,
            self.active_settings_tab,
            custom_tabs=custom_tabs,
            custom_renderers=custom_renderers
        )
    
    def draw_exit_confirm_dialog(self):
        """Teken exit confirmation dialog"""
        return self.dialog_renderer.draw_exit_confirm_dialog()
    
    def draw_new_game_confirm_dialog(self):
        """Teken new game confirmation dialog"""
        return self.dialog_renderer.draw_new_game_confirm_dialog()
    
    def highlight_squares(self, squares):
        """
        Highlight specifieke velden
        
        Args:
            squares: List van chess notaties zoals ['E4', 'E5']
        """
        # Splits squares in normale moves en captures
        self.highlighted_squares = []
        self.capture_squares = []
        
        for square in squares:
            # Check of er een vijandelijk stuk staat op deze square
            # chess.parse_square() verwacht lowercase notatie
            piece = self.engine.board.piece_at(chess.parse_square(square.lower()))
            if piece and piece.color != self.engine.board.turn:
                # Dit is een capture
                self.capture_squares.append(square)
            else:
                # Normale move
                self.highlighted_squares.append(square)
    
    def set_selected_piece(self, piece, from_square):
        """
        Zet het geselecteerde stuk
        
        Args:
            piece: chess.Piece object of None
            from_square: String zoals "E2" of None
        """
        self.selected_piece = piece
        self.selected_piece_from = from_square
    
    def set_last_move(self, from_square, to_square, intermediate=None):
        """Set laatste zet voor highlighting (intermediate parameter voor checkers compatibility)"""
        self.last_move_from = from_square
        self.last_move_to = to_square
        # Chess gebruikt geen intermediate, maar accepteer parameter voor compatibility
    
    def update_sensor_debug_states(self, sensor_states):
        """
        Update sensor states voor debug visualisatie
        
        Args:
            sensor_states: Dict met chess posities als keys, True/False als values
        """
        self.active_sensor_states = sensor_states
    
    def get_square_from_pos(self, pos):
        """
        Converteer muis positie naar chess square notatie
        
        Args:
            pos: (x, y) tuple van muis positie
            
        Returns:
            String zoals "E2" of None als niet op bord geklikt
        """
        return self.board_renderer.get_square_from_pos(pos)
    
    def draw(self, temp_message=None, temp_message_timer=0):
        """Teken complete GUI"""
        # Clear screen
        self.screen.fill(self.COLOR_BG)
        
        # Teken bord en stukken
        self.draw_board()
        self.draw_pieces()
        
        # Teken debug overlays (boven pieces)
        self.draw_debug_overlays()
        
        # Teken coördinaten alleen als setting aan staat
        if self.settings.get('show_coordinates', True, section='debug'):
            self.draw_coordinates()
        
        self.draw_sidebar()
        
        # Teken settings dialog indien nodig
        ok_button = None
        toggle_rect = None
        brightness_slider_rect = None
        debug_toggle_rect = None
        general_tab = None
        debug_tab = None
        vs_computer_toggle_rect = None
        stockfish_slider_rect = None
        tabs = None
        sliders = None
        toggles = None
        dropdowns = {}
        dropdown_items = []
        power_profiles = []
        screensaver_button = None
        if self.show_settings:
            settings_result = self.draw_settings_dialog()
            ok_button = settings_result['ok_button']
            tabs = settings_result['tabs']
            sliders = settings_result['sliders']
            toggles = settings_result['toggles']
            dropdowns = settings_result.get('dropdowns', {})
            dropdown_items = settings_result.get('dropdown_items', [])
            power_profiles = settings_result.get('power_profiles', [])
            screensaver_button = settings_result.get('screensaver_button')
            # Extract individual values for backwards compatibility
            toggle_rect = toggles.get('coordinates')
            debug_toggle_rect = toggles.get('debug_sensors')
            vs_computer_toggle_rect = toggles.get('vs_computer')
            brightness_slider_rect = sliders.get('brightness')
            stockfish_slider_rect = sliders.get('skill')  # or other stockfish slider
            general_tab = tabs.get('general')
            debug_tab = tabs.get('debug')
        
        # Teken exit confirmation dialog indien nodig
        exit_yes_button = None
        exit_no_button = None
        if self.show_exit_confirm:
            exit_yes_button, exit_no_button = self.draw_exit_confirm_dialog()
        
        # Teken stop game confirmation dialog indien nodig
        stop_game_yes_button = None
        stop_game_no_button = None
        if self.show_stop_game_confirm:
            stop_game_yes_button, stop_game_no_button = self.dialog_renderer.draw_stop_game_confirm_dialog()
        
        # Teken new game confirmation dialog indien nodig
        new_game_normal_button = None
        new_game_assisted_button = None
        new_game_cancel_button = None
        if self.show_new_game_confirm:
            new_game_normal_button, new_game_assisted_button, new_game_cancel_button = self.draw_new_game_confirm_dialog()
        
        # Teken skip setup step confirmation dialog indien nodig
        skip_setup_yes_button = None
        skip_setup_no_button = None
        if self.show_skip_setup_step_confirm:
            skip_setup_yes_button, skip_setup_no_button = self.dialog_renderer.draw_skip_setup_step_dialog()
        
        # Teken temp message bovenop alles (als actief en geen dialogs open)
        if temp_message and pygame.time.get_ticks() < temp_message_timer:
            # Niet tonen als er een dialog open is
            if not (self.show_settings or self.show_exit_confirm or self.show_new_game_confirm or self.show_stop_game_confirm or self.show_skip_setup_step_confirm):
                # Parse message: kan string, list of tuple (message, type) zijn
                if isinstance(temp_message, tuple):
                    message_text, notification_type = temp_message
                else:
                    message_text = temp_message
                    # Kies notification type op basis van message content
                    # Als message een list is, check de eerste regel
                    check_text = message_text[0] if isinstance(message_text, list) else message_text
                    if 'mismatch' in check_text.lower() or 'invalid' in check_text.lower():
                        notification_type = 'error'
                    else:
                        notification_type = 'warning'
                
                UIWidgets.draw_notification(self.screen, message_text, board_width=self.board_size, board_height=self.board_size, notification_type=notification_type)
        
        # Update display
        pygame.display.flip()
        
        return {
            'ok_button': ok_button,
            'tabs': tabs if self.show_settings else None,
            'sliders': sliders if self.show_settings else None,
            'toggles': toggles if self.show_settings else None,
            'dropdowns': dropdowns if self.show_settings else {},
            'dropdown_items': dropdown_items if self.show_settings else [],
            'power_profiles': power_profiles if self.show_settings else [],
            'screensaver_button': screensaver_button,
            'exit_yes': exit_yes_button,
            'exit_no': exit_no_button,
            'stop_game_yes': stop_game_yes_button,
            'stop_game_no': stop_game_no_button,
            'new_game_normal': new_game_normal_button,
            'new_game_assisted': new_game_assisted_button,
            'new_game_cancel': new_game_cancel_button,
            'skip_setup_yes': skip_setup_yes_button,
            'skip_setup_no': skip_setup_no_button
        }
    
    def handle_settings_click(self, pos):
        """Handle klik op settings button"""
        if self.settings_button.collidepoint(pos):
            self.show_settings = True
            # Kopieer huidige settings naar temp bij openen
            self.temp_settings = self.settings.get_temp_copy()
            return True
        return False
    
    def handle_exit_click(self, pos):
        """Handle klik op exit button"""
        if self.exit_button.collidepoint(pos):
            self.show_exit_confirm = True
            return True
        return False
    
    def handle_exit_yes_click(self, pos, yes_button):
        """Handle klik op Yes in exit confirmation"""
        if yes_button and yes_button.collidepoint(pos):
            return True
        return False
    
    def handle_exit_no_click(self, pos, no_button):
        """Handle klik op No in exit confirmation"""
        if no_button and no_button.collidepoint(pos):
            self.show_exit_confirm = False
            return True
        return False
    
    def handle_exit_click(self, pos):
        """Handle klik op exit button"""
        if self.exit_button.collidepoint(pos):
            self.show_exit_confirm = True
            return True
        return False
    
    def handle_exit_yes_click(self, pos, yes_button):
        """Handle klik op Yes in exit confirmation"""
        if yes_button and yes_button.collidepoint(pos):
            return True
        return False
    
    def handle_exit_no_click(self, pos, no_button):
        """Handle klik op No in exit confirmation"""
        if no_button and no_button.collidepoint(pos):
            self.show_exit_confirm = False
            return True
        return False
    
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
    
    def handle_stop_game_yes_click(self, pos, yes_button):
        """Handle klik op Yes in stop game confirmation"""
        if yes_button and yes_button.collidepoint(pos):
            return True
        return False
    
    def handle_stop_game_no_click(self, pos, no_button):
        """Handle klik op No in stop game confirmation"""
        if no_button and no_button.collidepoint(pos):
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
    
    # Delegeer alle event handling naar EventHandlers
    def handle_settings_click(self, pos):
        return self.events.handle_settings_click(pos)
    
    def handle_ok_click(self, pos, ok_button):
        return self.events.handle_ok_click(pos, ok_button)
    
    def handle_tab_click(self, pos, general_tab, debug_tab):
        return self.events.handle_tab_click(pos, general_tab, debug_tab)
    
    def handle_toggle_click(self, pos, toggle_rect):
        return self.events.handle_toggle_click(pos, toggle_rect)
    
    def handle_debug_toggle_click(self, pos, toggle_rect):
        return self.events.handle_debug_toggle_click(pos, toggle_rect)
    
    def handle_vs_computer_toggle_click(self, pos, toggle_rect):
        return self.events.handle_vs_computer_toggle_click(pos, toggle_rect)
    
    def handle_brightness_slider_click(self, pos, slider_rect):
        return self.events.handle_brightness_slider_click(pos, slider_rect)
    
    def handle_brightness_slider_drag(self, pos, slider_rect):
        return self.events.handle_brightness_slider_drag(pos, slider_rect)
    
    def stop_brightness_slider_drag(self):
        return self.events.stop_brightness_slider_drag()
    
    def handle_stockfish_slider_click(self, pos, slider_rect):
        return self.events.handle_stockfish_slider_click(pos, slider_rect)
    
    def handle_stockfish_slider_drag(self, pos, slider_rect):
        return self.events.handle_stockfish_slider_drag(pos, slider_rect)
    
    def stop_stockfish_slider_drag(self):
        return self.events.stop_stockfish_slider_drag()
    
    def handle_exit_click(self, pos):
        return self.events.handle_exit_click(pos)
    
    def handle_exit_yes_click(self, pos, yes_button):
        return self.events.handle_exit_yes_click(pos, yes_button)
    
    def handle_exit_no_click(self, pos, no_button):
        return self.events.handle_exit_no_click(pos, no_button)
    
    def quit(self):
        """Sluit GUI af"""
        pygame.quit()


