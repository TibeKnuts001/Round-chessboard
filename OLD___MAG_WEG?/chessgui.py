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
from lib.chessengine import ChessEngine
from lib.settings import Settings
from lib.gui.dialogs import DialogRenderer
from lib.gui.settings_dialog import SettingsDialog
from lib.gui.board import BoardRenderer
from lib.gui.sidebar import SidebarRenderer
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
        
        # Eerste rij (New Game, Exit)
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
        
        # Tweede rij (Settings, placeholder)
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
        self.show_power_dropdown = False  # Power profile dropdown open/gesloten
        self.highlighted_squares = []
        self.dragging_slider = False
        self.dragging_stockfish_slider = False
        self.selected_piece = None  # Opgepakte stuk (chess.Piece object)
        self.selected_piece_from = None  # Van welk veld opgepakt (bijv "E2")
        self.active_settings_tab = 'general'  # Active tab in settings ('general' of 'debug')
        self.active_sensor_states = {}  # Voor debug visualisatie
        
        # Renderers voor verschillende GUI componenten
        self.board_renderer = BoardRenderer(
            self.screen,
            self.board_size,
            self.square_size,
            self.font_small
        )
        
        self.sidebar_renderer = SidebarRenderer(
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
            self  # Pass GUI reference for dropdown state
        )
        
        # Event handlers (delegeer alle click/drag handling)
        self.events = EventHandlers(self)
    
    def draw_board(self):
        """Teken schaakbord"""
        self.board_renderer.draw_board(self.highlighted_squares, self.selected_piece_from)
    
    def draw_coordinates(self):
        """Teken coördinaten"""
        self.board_renderer.draw_coordinates()
    
    def draw_pieces(self):
        """Teken schaakstukken"""
        self.board_renderer.draw_pieces(self.engine.get_board())
    
    def draw_debug_overlays(self):
        """Teken debug overlays"""
        if self.settings.get('debug_sensors', False):
            self.board_renderer.draw_debug_overlays(self.active_sensor_states)
    
    def draw_sidebar(self):
        """Teken sidebar"""
        self.sidebar_renderer.draw_sidebar(
            self.engine,
            self.new_game_button,
            self.exit_button,
            self.settings_button
        )
    
    def draw_settings_dialog(self):
        """Teken settings dialog - delegeer naar settings_dialog renderer"""
        # Gebruik temp_settings als die bestaat, anders echte settings
        active_settings = self.temp_settings if self.temp_settings else self.settings
        return self.settings_dialog.draw(
            active_settings,
            self.active_settings_tab
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
        self.highlighted_squares = squares
    
    def set_selected_piece(self, piece, from_square):
        """
        Zet het geselecteerde stuk
        
        Args:
            piece: chess.Piece object of None
            from_square: String zoals "E2" of None
        """
        self.selected_piece = piece
        self.selected_piece_from = from_square
    
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
        if self.settings.get('show_coordinates', True):
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
        if self.show_settings:
            settings_result = self.draw_settings_dialog()
            ok_button = settings_result['ok_button']
            tabs = settings_result['tabs']
            sliders = settings_result['sliders']
            toggles = settings_result['toggles']
            dropdowns = settings_result.get('dropdowns', {})
            dropdown_items = settings_result.get('dropdown_items', [])
            power_profiles = settings_result.get('power_profiles', [])
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
        
        # Teken new game confirmation dialog indien nodig
        new_game_yes_button = None
        new_game_no_button = None
        if self.show_new_game_confirm:
            new_game_yes_button, new_game_no_button = self.draw_new_game_confirm_dialog()
        
        # Teken temp message bovenop alles (als actief en geen dialogs open)
        if temp_message and pygame.time.get_ticks() < temp_message_timer:
            # Niet tonen als er een dialog open is
            if not (self.show_settings or self.show_exit_confirm or self.show_new_game_confirm):
                self._draw_temp_message(temp_message)
        
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
            'exit_yes': exit_yes_button,
            'exit_no': exit_no_button,
            'new_game_yes': new_game_yes_button,
            'new_game_no': new_game_no_button
        }
    
    def handle_settings_click(self, pos):
        """Handle klik op settings button"""
        if self.settings_button.collidepoint(pos):
            self.show_settings = True
            # Kopieer huidige settings naar temp bij openen
            self.temp_settings = self.settings.settings.copy()
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
        """Handle klik op new game button"""
        if self.new_game_button.collidepoint(pos):
            self.show_new_game_confirm = True
            return True
        return False
    
    def handle_new_game_yes_click(self, pos, yes_button):
        """Handle klik op Yes in new game confirmation"""
        if yes_button and yes_button.collidepoint(pos):
            return True
        return False
    
    def handle_new_game_no_click(self, pos, no_button):
        """Handle klik op No in new game confirmation"""
        if no_button and no_button.collidepoint(pos):
            self.show_new_game_confirm = False
            return True
        return False
    
    def _draw_temp_message(self, message):
        """Teken tijdelijk bericht overlay"""
        # Kleinere overlay boven in het midden
        board_width = 800
        overlay_width = 350
        overlay_height = 80
        overlay_x = (board_width - overlay_width) // 2
        overlay_y = 50
        
        # Achtergrond box (donkerrood/oranje voor waarschuwing)
        pygame.draw.rect(self.screen, (80, 40, 20), 
                        (overlay_x, overlay_y, overlay_width, overlay_height), 
                        border_radius=12)
        
        # Border (oranje)
        pygame.draw.rect(self.screen, (255, 150, 0), 
                        (overlay_x, overlay_y, overlay_width, overlay_height), 4, border_radius=12)
        
        # Warning icon (!)  
        font_large = pygame.font.Font(None, 64)
        icon = font_large.render("!", True, (255, 200, 0))
        icon_rect = icon.get_rect(center=(overlay_x + 30, overlay_y + overlay_height // 2))
        self.screen.blit(icon, icon_rect)
        
        # Message tekst
        font = pygame.font.Font(None, 26)
        text = font.render(message, True, (255, 255, 255))
        text_rect = text.get_rect(center=(overlay_x + overlay_width // 2 + 10, overlay_y + overlay_height // 2))
        self.screen.blit(text, text_rect)
    
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
    
    def handle_new_game_click(self, pos):
        return self.events.handle_new_game_click(pos)
    
    def handle_new_game_yes_click(self, pos, yes_button):
        return self.events.handle_new_game_yes_click(pos, yes_button)
    
    def handle_new_game_no_click(self, pos, no_button):
        return self.events.handle_new_game_no_click(pos, no_button)
    
    def quit(self):
        """Sluit GUI af"""
        pygame.quit()

