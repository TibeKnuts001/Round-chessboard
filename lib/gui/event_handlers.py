#!/usr/bin/env python3
"""
Event Handlers Module

Centraliseert alle user input verwerking voor de chess GUI.
Uitgesloten uit chessgui.py voor betere separation of concerns.

Verwerkte events:
- Mouse clicks: buttons, toggles, sliders, dialogs
- Mouse drags: brightness slider, difficulty slider
- Keyboard: ESC voor dialogs sluiten

Handler categorieën:
1. Settings Dialog
   - Tab switching (General/Stockfish/Debug)
   - Toggle clicks (coordinates, debug sensors, vs computer)
   - Slider clicks + drags (brightness, skill, think_time, depth, threads)
   - OK button (save settings)

2. Confirmation Dialogs
   - Exit confirmation (Ja/Nee)
   - New game confirmation (Ja/Nee)

3. Temp Settings Pattern
   - Alle wijzigingen gaan naar gui.temp_settings
   - Pas bij OK wordt settings.settings ge-update
   - ESC/Cancel: temp_settings cleared, changes lost

Architectuur:
- EventHandlers krijgt gui instance als parameter
- Manipuleert gui state via self.gui.* properties
- Returns booleans voor action completion (True = handled)

Hoofdklasse:
- EventHandlers: Bevat alle handle_*_click/drag methods

Wordt gebruikt door: ChessGUI (via self.events delegation)
"""

import pygame
from lib.settings import Settings


class EventHandlers:
    """Handles all GUI event interactions"""
    
    def __init__(self, gui):
        """
        Args:
            gui: ChessGUI instance (parent)
        """
        self.gui = gui
    
    # Settings dialog handlers
    
    def handle_settings_click(self, pos):
        """Handle klik op settings button"""
        if self.gui.settings_button.collidepoint(pos):
            self.gui.show_settings = True
            # Kopieer huidige settings naar temp bij openen
            self.gui.temp_settings = self.gui.settings.get_temp_copy()
            return True
        return False
    
    def handle_ok_click(self, pos, ok_button):
        """Handle klik op OK button in settings"""
        if ok_button and ok_button.collidepoint(pos):
            # Sla alle tijdelijke settings permanent op
            if self.gui.temp_settings:
                # Update settings met temp values (merge nested dicts)
                for section, section_data in self.gui.temp_settings.items():
                    if isinstance(section_data, dict):
                        # Update sectie (hardware, debug, chess, checkers)
                        if section not in self.gui.settings.settings:
                            self.gui.settings.settings[section] = {}
                        self.gui.settings.settings[section].update(section_data)
                    else:
                        # Backward compatibility: directe key
                        self.gui.settings.settings[section] = section_data
                
                self.gui.settings.save()
                self.gui.temp_settings = {}
            
            self.gui.show_settings = False
            return True
        return False
    
    def handle_tab_click(self, pos, tabs_dict):
        """Handle klik op tab
        
        Args:
            pos: Mouse position (x, y)
            tabs_dict: Dict met tab keys -> rects (disabled tabs hebben None als rect)
        
        Returns:
            bool: True if tab was clicked, False otherwise
        """
        # Check alle tabs generiek (loop over dict)
        for tab_key, tab_rect in tabs_dict.items():
            if tab_rect and tab_rect.collidepoint(pos):
                self.gui.active_settings_tab = tab_key
                return True
        
        return False
    
    # Toggle handlers
    
    def handle_toggle_click(self, pos, toggle_rect):
        """Handle klik op show coordinates toggle switch"""
        if toggle_rect and toggle_rect.collidepoint(pos):
            # Toggle tijdelijk (niet permanent opslaan)
            if not self.gui.temp_settings:
                self.gui.temp_settings = self.gui.settings.get_temp_copy()
            current_value = Settings.get_from_dict(self.gui.temp_settings, 'show_coordinates', True)
            Settings.set_in_dict(self.gui.temp_settings, 'show_coordinates', not current_value)
            return True
        return False
    
    def handle_debug_toggle_click(self, pos, toggle_rect):
        """Handle klik op debug toggle switch"""
        if toggle_rect and toggle_rect.collidepoint(pos):
            # Toggle tijdelijk (niet permanent opslaan)
            if not self.gui.temp_settings:
                self.gui.temp_settings = self.gui.settings.get_temp_copy()
            current_value = Settings.get_from_dict(self.gui.temp_settings, 'debug_sensors', False)
            Settings.set_in_dict(self.gui.temp_settings, 'debug_sensors', not current_value)
            return True
        return False
    
    def handle_vs_computer_toggle_click(self, pos, toggle_rect):
        """Handle klik op VS Computer toggle switch"""
        if toggle_rect and toggle_rect.collidepoint(pos):
            # Toggle tijdelijk (niet permanent opslaan)
            if not self.gui.temp_settings:
                self.gui.temp_settings = self.gui.settings.get_temp_copy()
            current_value = Settings.get_from_dict(self.gui.temp_settings, 'play_vs_computer', False)
            Settings.set_in_dict(self.gui.temp_settings, 'play_vs_computer', not current_value)
            return True
        return False
    
    def handle_strict_touch_move_toggle_click(self, pos, toggle_rect):
        """Handle klik op strict touch-move toggle switch"""
        if toggle_rect and toggle_rect.collidepoint(pos):
            # Toggle tijdelijk (niet permanent opslaan)
            if not self.gui.temp_settings:
                self.gui.temp_settings = self.gui.settings.get_temp_copy()
            current_value = Settings.get_from_dict(self.gui.temp_settings, 'strict_touch_move', False)
            Settings.set_in_dict(self.gui.temp_settings, 'strict_touch_move', not current_value)
            return True
        return False
    
    def handle_use_worstfish_toggle_click(self, pos, toggle_rect):
        """Handle klik op use worstfish toggle switch"""
        if toggle_rect and toggle_rect.collidepoint(pos):
            # Toggle tijdelijk (niet permanent opslaan)
            if not self.gui.temp_settings:
                self.gui.temp_settings = self.gui.settings.get_temp_copy()
            current_value = Settings.get_from_dict(self.gui.temp_settings, 'use_worstfish', False)
            Settings.set_in_dict(self.gui.temp_settings, 'use_worstfish', not current_value)
            return True
        return False
    
    def handle_validate_board_state_toggle_click(self, pos, toggle_rect):
        """Handle klik op validate board state toggle switch"""
        if toggle_rect and toggle_rect.collidepoint(pos):
            # Toggle tijdelijk (niet permanent opslaan)
            if not self.gui.temp_settings:
                self.gui.temp_settings = self.gui.settings.get_temp_copy()
            current_value = Settings.get_from_dict(self.gui.temp_settings, 'validate_board_state', True)
            Settings.set_in_dict(self.gui.temp_settings, 'validate_board_state', not current_value)
            return True
        return False
    
    def handle_screensaver_audio_toggle_click(self, pos, toggle_rect):
        """Handle klik op screensaver audio toggle switch"""
        if toggle_rect and toggle_rect.collidepoint(pos):
            # Toggle tijdelijk (niet permanent opslaan)
            if not self.gui.temp_settings:
                self.gui.temp_settings = self.gui.settings.get_temp_copy()
            current_value = Settings.get_from_dict(self.gui.temp_settings, 'screensaver_audio', True, section='general')
            Settings.set_in_dict(self.gui.temp_settings, 'screensaver_audio', not current_value, section='general')
            return True
        return False
    
    # Checkers-specific toggle handlers
    
    def handle_vs_computer_checkers_toggle_click(self, pos, toggle_rect):
        """Handle klik op VS Computer toggle switch (checkers)"""
        if toggle_rect and toggle_rect.collidepoint(pos):
            if not self.gui.temp_settings:
                self.gui.temp_settings = self.gui.settings.get_temp_copy()
            current_value = Settings.get_from_dict(self.gui.temp_settings, 'play_vs_computer', False, section='checkers')
            Settings.set_in_dict(self.gui.temp_settings, 'play_vs_computer', not current_value, section='checkers')
            return True
        return False
    
    def handle_strict_touch_move_checkers_toggle_click(self, pos, toggle_rect):
        """Handle klik op strict touch-move toggle switch (checkers)"""
        if toggle_rect and toggle_rect.collidepoint(pos):
            if not self.gui.temp_settings:
                self.gui.temp_settings = self.gui.settings.get_temp_copy()
            current_value = Settings.get_from_dict(self.gui.temp_settings, 'strict_touch_move', False, section='checkers')
            Settings.set_in_dict(self.gui.temp_settings, 'strict_touch_move', not current_value, section='checkers')
            return True
        return False
    
    # Slider handlers
    
    def handle_slider_drag(self, pos, sliders_dict):
        """Handle drag for any active slider
        
        Args:
            pos: Mouse position (x, y)
            sliders_dict: Dict with slider rects {'brightness': rect, 'skill': rect, ...}
        
        Returns:
            bool: True if any slider drag was handled
        """
        if not self.gui.dragging_slider:
            return False
        
        # Map slider types to their settings and ranges
        slider_configs = {
            'brightness': ('brightness', 0, 100),
            'skill': ('stockfish_skill_level', 0, 20),
            'think_time': ('stockfish_think_time', 500, 10000),
            'depth': ('stockfish_depth', 5, 25),
            'threads': ('stockfish_threads', 1, 4),
            'ai_difficulty': ('ai_difficulty', 1, 10),
            'ai_think_time': ('ai_think_time', 500, 5000),
        }
        
        slider_type = self.gui.dragging_slider
        if slider_type in slider_configs and slider_type in sliders_dict:
            setting_key, min_val, max_val = slider_configs[slider_type]
            slider_rect = sliders_dict.get(slider_type)
            return self._handle_slider_drag(pos, slider_rect, slider_type, setting_key, min_val, max_val)
        
        return False
    
    def stop_slider_drag(self):
        """Stop any active slider drag"""
        self.gui.dragging_slider = None
    
    def _handle_slider_click(self, pos, slider_rect, slider_type):
        """Generic slider click handler - sets dragging state
        
        Args:
            pos: Mouse position (x, y)
            slider_rect: Pygame rect for slider interaction area
            slider_type: String identifier ('brightness', 'skill', 'think_time', 'depth', 'threads')
        
        Returns:
            bool: True if slider was clicked, False otherwise
        """
        if slider_rect and slider_rect.collidepoint(pos):
            self.gui.dragging_slider = slider_type
            return True
        return False
    
    def _handle_slider_drag(self, pos, slider_rect, slider_type, setting_key, min_val, max_val):
        """Generic slider drag handler
        
        Args:
            pos: Mouse position (x, y)
            slider_rect: Pygame rect for slider interaction area
            slider_type: String identifier to check against self.gui.dragging_slider
            setting_key: Settings dict key to update
            min_val: Minimum slider value
            max_val: Maximum slider value
        
        Returns:
            bool: True if drag was handled, False otherwise
        """
        if self.gui.dragging_slider == slider_type and slider_rect:
            self._update_slider_value(pos, slider_rect, setting_key, min_val, max_val)
            return True
        return False
    
    def _update_slider_value(self, pos, slider_rect, setting_key, min_val, max_val):
        """Update slider value based on mouse position
        
        Args:
            pos: Mouse position (x, y)
            slider_rect: Pygame rect for slider interaction area
            setting_key: Settings dict key to update
            min_val: Minimum slider value
            max_val: Maximum slider value
        """
        knob_radius = 18
        slider_start_x = slider_rect.x + knob_radius
        slider_width = slider_rect.width - 2 * knob_radius
        
        # Calculate new value based on position
        relative_x = pos[0] - slider_start_x
        # Clamp relative_x to prevent value from going outside bounds
        relative_x = max(0, min(slider_width, relative_x))
        
        value_range = max_val - min_val
        value = int((relative_x / slider_width) * value_range) + min_val
        value = max(min_val, min(max_val, value))  # Clamp between min and max
        
        # Store temporarily (not permanent)
        if not self.gui.temp_settings:
            self.gui.temp_settings = self.gui.settings.get_temp_copy()
        Settings.set_in_dict(self.gui.temp_settings, setting_key, value)
    
    def handle_brightness_slider_click(self, pos, slider_rect):
        """Handle brightness slider click to start dragging"""
        if self._handle_slider_click(pos, slider_rect, 'brightness'):
            self._update_brightness_from_pos(pos, slider_rect)
            return True
        return False
    
    def handle_validate_board_state_toggle_click(self, pos, toggle_rect):
        """Handle klik op validate board state toggle switch"""
        if toggle_rect is None:
            return False
        
        if toggle_rect.collidepoint(pos):
            current_value = Settings.get_from_dict(self.gui.temp_settings, 'validate_board_state', False)
            Settings.set_in_dict(self.gui.temp_settings, 'validate_board_state', not current_value)
            print(f"Validate board state toggled: {not current_value}")
            return True
        return False
    
    def handle_brightness_slider_drag(self, pos, slider_rect):
        """Handle brightness slider drag (tijdens slepen)"""
        if self.gui.dragging_slider == 'brightness' and slider_rect:
            self._update_brightness_from_pos(pos, slider_rect)
            return True
        return False
    
    def stop_slider_drag(self):
        """Stop any slider drag"""
        self.gui.dragging_slider = None
    
    def _update_brightness_from_pos(self, pos, slider_rect):
        """Update brightness op basis van muis positie"""
        # Haal knob radius uit rect (aangenomen 18px knob)
        knob_radius = 18
        # Slider begint knob_radius pixels in de interaction rect
        slider_start_x = slider_rect.x + knob_radius
        slider_width = slider_rect.width - 2 * knob_radius
        
        # Bereken nieuwe brightness waarde (0-100)
        relative_x = pos[0] - slider_start_x
        brightness = int((relative_x / slider_width) * 100)
        brightness = max(0, min(100, brightness))  # Clamp tussen 0-100
        
        # Cap brightness based on power profile
        if not self.gui.temp_settings:
            self.gui.temp_settings = self.gui.settings.get_temp_copy()
        
        max_brightness = self.gui.settings.get_max_brightness()
        # Als temp_settings een ander power profile heeft, gebruik die
        power_profile = Settings.get_from_dict(self.gui.temp_settings, 'power_profile', 1.5)
        max_brightness = Settings.POWER_PROFILES.get(power_profile, 60)
        
        brightness = min(brightness, max_brightness)
        
        # Sla tijdelijk op (niet permanent)
        Settings.set_in_dict(self.gui.temp_settings, 'brightness', brightness)
    
    def handle_skill_slider_click(self, pos, slider_rect):
        """Handle stockfish skill slider click to start dragging"""
        if self._handle_slider_click(pos, slider_rect, 'skill'):
            self._update_stockfish_skill_from_pos(pos, slider_rect)
            return True
        return False
    
    def handle_skill_slider_drag(self, pos, slider_rect):
        """Handle stockfish skill slider drag"""
        if self.gui.dragging_slider == 'skill' and slider_rect:
            self._update_stockfish_skill_from_pos(pos, slider_rect)
            return True
        return False
    
    def _update_stockfish_skill_from_pos(self, pos, slider_rect):
        """Update stockfish skill level op basis van muis positie"""
        knob_radius = 18
        slider_start_x = slider_rect.x + knob_radius
        slider_width = slider_rect.width - 2 * knob_radius
        
        # Bereken nieuwe skill level (0-20)
        relative_x = pos[0] - slider_start_x
        skill_level = int((relative_x / slider_width) * 20)
        skill_level = max(0, min(20, skill_level))  # Clamp tussen 0-20
        
        # Sla tijdelijk op (niet permanent)
        if not self.gui.temp_settings:
            self.gui.temp_settings = self.gui.settings.get_temp_copy()
        self.gui.temp_settings['stockfish_skill_level'] = skill_level
    
    # Stockfish tab slider handlers
    
    def handle_think_time_slider_click(self, pos, slider_rect):
        """Handle think time slider click to start dragging"""
        if self._handle_slider_click(pos, slider_rect, 'think_time'):
            self._handle_slider_drag(pos, slider_rect, 'think_time', 'stockfish_think_time', 500, 5000)
            return True
        return False
    
    def handle_think_time_slider_drag(self, pos, slider_rect):
        """Handle think time slider drag"""
        return self._handle_slider_drag(pos, slider_rect, 'think_time', 'stockfish_think_time', 500, 5000)
    
    def handle_depth_slider_click(self, pos, slider_rect):
        """Handle depth slider click to start dragging"""
        if self._handle_slider_click(pos, slider_rect, 'depth'):
            self._handle_slider_drag(pos, slider_rect, 'depth', 'stockfish_depth', 5, 25)
            return True
        return False
    
    def handle_depth_slider_drag(self, pos, slider_rect):
        """Handle depth slider drag"""
        return self._handle_slider_drag(pos, slider_rect, 'depth', 'stockfish_depth', 5, 25)
    
    def handle_threads_slider_click(self, pos, slider_rect):
        """Handle threads slider click to start dragging"""
        if self._handle_slider_click(pos, slider_rect, 'threads'):
            self._handle_slider_drag(pos, slider_rect, 'threads', 'stockfish_threads', 1, 4)
            return True
        return False
    
    def handle_threads_slider_drag(self, pos, slider_rect):
        """Handle threads slider drag"""
        return self._handle_slider_drag(pos, slider_rect, 'threads', 'stockfish_threads', 1, 4)
    
    # Dropdown handlers
    
    def handle_power_profile_dropdown_click(self, pos, dropdown_rect):
        """Handle power profile dropdown button click - toggle open/close
        
        Args:
            pos: Mouse position
            dropdown_rect: Dropdown button rect
        
        Returns:
            bool: True if dropdown button was clicked
        """
        if dropdown_rect and dropdown_rect.collidepoint(pos):
            # Toggle dropdown open/closed
            self.gui.show_power_dropdown = not self.gui.show_power_dropdown
            return True
        return False
    
    def handle_power_profile_item_click(self, pos, dropdown_items):
        """Handle click on power profile dropdown item
        
        Args:
            pos: Mouse position
            dropdown_items: List of (value, rect, text, is_selected) tuples
        
        Returns:
            bool: True if an item was clicked
        """
        if not dropdown_items:
            return False
        
        for item in dropdown_items:
            # Unpack tuple (can be old format with 2 or new format with 4 elements)
            if len(item) == 4:
                value, rect, text, is_selected = item
            else:
                value, rect = item
            
            if rect.collidepoint(pos):
                if not self.gui.temp_settings:
                    self.gui.temp_settings = self.gui.settings.get_temp_copy()
                
                # Update power profile
                Settings.set_in_dict(self.gui.temp_settings, 'power_profile', value)
                
                # Cap brightness if needed
                max_brightness = Settings.POWER_PROFILES.get(value, 60)
                current_brightness = Settings.get_from_dict(self.gui.temp_settings, 'brightness', 20)
                if current_brightness > max_brightness:
                    Settings.set_in_dict(self.gui.temp_settings, 'brightness', max_brightness)
                
                # Close dropdown
                self.gui.show_power_dropdown = False
                return True
        
        return False
    
    # Exit confirmation handlers
    
    def handle_exit_click(self, pos):
        """Handle klik op exit button"""
        if self.gui.exit_button.collidepoint(pos):
            self.gui.show_exit_confirm = True
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
            self.gui.show_exit_confirm = False
            return True
        return False
    
    # New game confirmation handlers
    
    def handle_new_game_click(self, pos):
        """Handle klik op new game button"""
        if self.gui.new_game_button.collidepoint(pos):
            self.gui.show_new_game_confirm = True
            return True
        return False
    
    def handle_new_game_normal_click(self, pos, button):
        """Handle klik op Normal in new game confirmation"""
        if button and button.collidepoint(pos):
            self.gui.assisted_setup_mode = False
            return True
        return False
    
    def handle_new_game_assisted_click(self, pos, button):
        """Handle klik op Assisted in new game confirmation"""
        if button and button.collidepoint(pos):
            self.gui.assisted_setup_mode = True
            self.gui.assisted_setup_step = 0
            self.gui.assisted_setup_waiting = True
            return True
        return False
    
    def handle_new_game_cancel_click(self, pos, button):
        """Handle klik op Cancel in new game confirmation"""
        if button and button.collidepoint(pos):
            self.gui.show_new_game_confirm = False
            return True
        return False
