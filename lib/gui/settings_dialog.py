#!/usr/bin/env python3
"""
Settings Dialog

Game-agnostic settings dialog met base tabs (General, Debug).
Games kunnen custom tabs toevoegen via custom_tabs en custom_renderers parameters.
"""

import pygame
from lib.gui.widgets import UIWidgets


class SettingsDialog:
    """Settings dialog renderer - game agnostic base"""
    
    def __init__(self, screen, screen_width, screen_height, font, font_small, gui=None):
        """
        Args:
            screen: Pygame screen surface
            screen_width: Screen width
            screen_height: Screen height
            font: Main font
            font_small: Small font
            gui: Reference to GUI instance (voor dropdown state etc)
        """
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = font
        self.font_small = font_small
        self.gui = gui
    
    def _draw_overlay(self):
        """Teken semi-transparante overlay"""
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
    
    def draw(self, settings, active_tab, custom_tabs=None, custom_renderers=None):
        """
        Teken settings dialog (game-agnostic)
        
        Args:
            settings: Settings dict
            active_tab: Active tab name
            custom_tabs: Optional list van (tab_key, tab_label, is_enabled) voor game-specifieke tabs
            custom_renderers: Optional dict {tab_key: render_function(dialog_x, content_y, settings, result)}
        
        Returns:
            Dict met UI elements voor event handling
        """
        self._draw_overlay()
        
        # Dialog box
        dialog_width = 600
        dialog_height = 500
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(self.screen, UIWidgets.COLOR_WHITE, dialog_rect, border_radius=15)
        
        # Title
        title = self.font.render("Settings", True, UIWidgets.COLOR_BLACK)
        title_rect = title.get_rect(center=(self.screen_width // 2, dialog_y + 30))
        self.screen.blit(title, title_rect)
        
        # Tab list (base tabs + optional custom tabs)
        debug_unlocked = self.gui and getattr(self.gui, 'debug_unlocked', False)
        base_tabs = [
            ('general', 'General', True),
            ('sound', 'Sound', True),
        ]
        if debug_unlocked:
            base_tabs.append(('debug', 'Debug', True))
        
        if custom_tabs:
            # Insert custom tabs between general and sound, keep debug at end if unlocked
            tab_list = [base_tabs[0]] + custom_tabs + [base_tabs[1]]
            if debug_unlocked:
                tab_list.append(base_tabs[2])
        else:
            tab_list = base_tabs
        
        # Draw tabs
        tab_y = dialog_y + 70
        tab_width = 100
        tab_height = 40
        tab_spacing = 6
        
        result = {
            'tabs': {},
            'sliders': {},
            'toggles': {},
            'dropdowns': {},
            'title_rect': title_rect,  # Voor secret debug unlock gesture
            'screensaver_button': None,  # Default None, wordt gezet in debug tab
            'assisted_setup_button': None,  # Default None, wordt gezet in general tab
            'tutorial_button': None,  # Default None, wordt gezet in general tab
            'check_updates_button': None  # Default None, wordt gezet in debug tab
        }
        
        start_x = dialog_x + (dialog_width - (len(tab_list) * (tab_width + tab_spacing) - tab_spacing)) // 2
        
        for i, (tab_name, tab_label, is_enabled) in enumerate(tab_list):
            tab_x = start_x + i * (tab_width + tab_spacing)
            tab_rect = pygame.Rect(tab_x, tab_y, tab_width, tab_height)
            
            UIWidgets.draw_tab(
                self.screen,
                tab_rect,
                tab_label,
                active_tab == tab_name,
                is_enabled,
                self.font_small
            )
            
            # Disabled tabs returnen None zodat ze niet clickbaar zijn
            result['tabs'][tab_name] = tab_rect if is_enabled else None
        
        # Content area
        content_y = tab_y + tab_height + 30
        
        # Draw tab content (base tabs or custom)
        if custom_renderers and active_tab in custom_renderers:
            custom_renderers[active_tab](dialog_x, content_y, settings, result)
        elif active_tab == 'general':
            self._draw_general_tab(dialog_x, content_y, settings, result)
        elif active_tab == 'sound':
            self._draw_sound_tab(dialog_x, content_y, settings, result)
        elif active_tab == 'debug':
            self._draw_debug_tab(dialog_x, content_y, settings, result)
        
        # OK button
        ok_button = UIWidgets.draw_button(
            self.screen,
            pygame.Rect(
                self.screen_width // 2 - 75,
                dialog_y + dialog_height - 70,
                150,
                50
            ),
            "OK",
            self.font,
            is_primary=True
        )
        result['ok_button'] = ok_button
        
        # Draw dropdown list items AFTER OK button (so dropdown appears on top)
        if result.get('dropdown_items'):
            for val, item_rect, text, is_selected in result['dropdown_items']:
                # Background
                if is_selected:
                    pygame.draw.rect(self.screen, (200, 220, 255), item_rect)
                else:
                    pygame.draw.rect(self.screen, (250, 250, 250), item_rect)
                
                # Border
                pygame.draw.rect(self.screen, (180, 180, 180), item_rect, width=1)
                
                # Text
                item_text = self.font_small.render(text, True, UIWidgets.COLOR_BLACK)
                self.screen.blit(item_text, (item_rect.x + 10, item_rect.y + 8))
        
        return result
    
    def _draw_sound_tab(self, dialog_x, content_y, settings, result):
        """Teken sound tab met volume sliders"""
        y_pos = content_y
        label_width = 210
        label_x = dialog_x + 30
        widget_x = label_x + label_width + 20
        
        # Effects Volume slider
        effects_volume = settings.get('general', {}).get('effects_volume', 80)
        effects_label = self.font_small.render("Effects Volume", True, UIWidgets.COLOR_BLACK)
        self.screen.blit(effects_label, (label_x, y_pos + 8))
        
        desc = self.font_small.render("Geluid van zetten, schaak, mat", True, (140, 140, 140))
        self.screen.blit(desc, (label_x, y_pos + 28))
        
        effects_slider_rect = UIWidgets.draw_slider(
            self.screen,
            widget_x,
            y_pos,
            200,
            effects_volume,
            0,
            100,
            f"{effects_volume}%",
            self.font_small
        )
        result['sliders']['effects_volume'] = effects_slider_rect
        
        y_pos += 85
        
        # Screensaver Music Volume slider
        music_volume = settings.get('general', {}).get('music_volume', 80)
        music_label = self.font_small.render("Screensaver Music Volume", True, UIWidgets.COLOR_BLACK)
        self.screen.blit(music_label, (label_x, y_pos + 8))
        
        desc2 = self.font_small.render("Achtergrondmuziek tijdens screensaver", True, (140, 140, 140))
        self.screen.blit(desc2, (label_x, y_pos + 28))
        
        music_slider_rect = UIWidgets.draw_slider(
            self.screen,
            widget_x,
            y_pos,
            200,
            music_volume,
            0,
            100,
            f"{music_volume}%",
            self.font_small
        )
        result['sliders']['music_volume'] = music_slider_rect
    
    def _draw_general_tab(self, dialog_x, content_y, settings, result):
        """Teken general tab (hardware settings - shared)"""
        y_pos = content_y
        label_width = 140
        label_x = dialog_x + 30
        widget_x = label_x + label_width + 20
        
        # Power Profile dropdown
        power_label = self.font_small.render("Power Profile", True, UIWidgets.COLOR_BLACK)
        self.screen.blit(power_label, (label_x, y_pos + 8))
        
        power_profiles = [
            (0.5, "0.5A (Low Power)"),
            (1.0, "1.0A (Medium)"),
            (1.5, "1.5A (Standard)"),
            (2.0, "2.0A (High)"),
            (2.5, "2.5A (Maximum)")
        ]
        
        current_power = settings.get('hardware', {}).get('power_profile', 1.5)
        current_text = next((text for val, text in power_profiles if val == current_power), "1.5A (Standard)")
        is_open = hasattr(self.gui, 'show_power_dropdown') and self.gui.show_power_dropdown
        
        dropdown_rect = UIWidgets.draw_dropdown(
            self.screen,
            widget_x,
            y_pos,
            200,
            40,
            current_text,
            is_open,
            self.font_small
        )
        result['dropdowns']['power_profile'] = dropdown_rect
        
        dropdown_y = y_pos
        y_pos += 70
        
        # LED Brightness slider
        brightness_label = self.font_small.render("LED Brightness", True, UIWidgets.COLOR_BLACK)
        self.screen.blit(brightness_label, (label_x, y_pos + 8))
        
        from lib.settings import Settings
        max_brightness = Settings.POWER_PROFILES.get(current_power, 60)
        brightness = min(settings.get('hardware', {}).get('brightness', 20), max_brightness)
        
        brightness_slider_rect = UIWidgets.draw_slider(
            self.screen,
            widget_x,
            y_pos,
            200,
            brightness,
            0,
            100,
            f"{brightness}%",
            self.font_small
        )
        
        # Store dropdown items (render later on top)
        dropdown_items = []
        if is_open:
            item_height = 35
            list_y = dropdown_y + 40
            
            for i, (val, text) in enumerate(power_profiles):
                item_rect = pygame.Rect(widget_x, list_y + i * item_height, 200, item_height)
                is_selected = (val == current_power)
                dropdown_items.append((val, item_rect, text, is_selected))
        
        # Update result dict
        result['dropdown_items'] = dropdown_items
        result['sliders']['brightness'] = brightness_slider_rect
        result['power_profiles'] = power_profiles
        result['max_brightness'] = max_brightness
        
        y_pos += 70
        
        # Screensaver Audio toggle
        audio_toggle_rect = UIWidgets.draw_toggle(
            self.screen,
            label_x,
            y_pos,
            settings.get('general', {}).get('screensaver_audio', True),
            self.font_small
        )
        
        audio_label = self.font_small.render("Screensaver Audio", True, UIWidgets.COLOR_BLACK)
        self.screen.blit(audio_label, (audio_toggle_rect.right + 15, y_pos + 8))
        
        result['toggles']['screensaver_audio'] = audio_toggle_rect
        
        y_pos += 70
        
        # Tutorial button (left)
        tutorial_button_rect = pygame.Rect(label_x, y_pos, 250, 45)
        tutorial_button = UIWidgets.draw_button(
            self.screen,
            tutorial_button_rect,
            "Show Board Tutorial",
            self.font_small
        )
        result['tutorial_button'] = tutorial_button
        
        # Assisted Setup button (right, next to tutorial) - disabled when no game started
        game_started = self.gui and getattr(self.gui, 'game_started', False)
        assisted_setup_button_rect = pygame.Rect(label_x + 270, y_pos, 250, 45)
        assisted_setup_button = UIWidgets.draw_button(
            self.screen,
            assisted_setup_button_rect,
            "Assisted Setup",
            self.font_small,
            is_primary=False,
            disabled=not game_started
        )
        result['assisted_setup_button'] = assisted_setup_button if game_started else None
    
    def _draw_debug_tab(self, dialog_x, content_y, settings, result):
        """Teken debug tab (debug settings - shared)"""
        y_pos = content_y
        toggle_x = dialog_x + 50
        
        # Debug sensors toggle
        debug_toggle_rect = UIWidgets.draw_toggle(
            self.screen,
            toggle_x,
            y_pos,
            settings.get('debug', {}).get('debug_sensors', False),
            self.font_small
        )
        
        label = self.font_small.render("Show sensor detection (yellow M)", True, UIWidgets.COLOR_BLACK)
        self.screen.blit(label, (debug_toggle_rect.right + 15, y_pos + 8))
        
        result['toggles']['debug_sensors'] = debug_toggle_rect
        
        y_pos += 55
        
        # Validate board state toggle
        validate_toggle_rect = UIWidgets.draw_toggle(
            self.screen,
            toggle_x,
            y_pos,
            settings.get('debug', {}).get('validate_board_state', True),
            self.font_small
        )
        
        label = self.font_small.render("Validate Board State", True, UIWidgets.COLOR_BLACK)
        self.screen.blit(label, (validate_toggle_rect.right + 15, y_pos + 8))
        
        result['toggles']['validate_board_state'] = validate_toggle_rect
        
        y_pos += 55

        # Allow Force Quit toggle
        force_quit_toggle_rect = UIWidgets.draw_toggle(
            self.screen,
            toggle_x,
            y_pos,
            settings.get('debug', {}).get('allow_force_quit', False),
            self.font_small
        )
        label = self.font_small.render("Show Force-Quit in exit popup", True, UIWidgets.COLOR_BLACK)
        self.screen.blit(label, (force_quit_toggle_rect.right + 15, y_pos + 8))
        result['toggles']['allow_force_quit'] = force_quit_toggle_rect

        y_pos += 55
        button_width = 185
        button_height = 45
        button_spacing = 20
        total_width = button_width * 2 + button_spacing
        left_x = dialog_x + (500 - total_width) // 2
        right_x = left_x + button_width + button_spacing
        
        screensaver_button_rect = pygame.Rect(left_x, y_pos, button_width, button_height)
        screensaver_button = UIWidgets.draw_button(
            self.screen,
            screensaver_button_rect,
            "Start Screensaver",
            self.font_small,
            is_primary=True
        )
        result['screensaver_button'] = screensaver_button
        
        check_updates_button_rect = pygame.Rect(right_x, y_pos, button_width, button_height)
        check_updates_button = UIWidgets.draw_button(
            self.screen,
            check_updates_button_rect,
            "Check for Updates",
            self.font_small,
            is_primary=False
        )
        result['check_updates_button'] = check_updates_button
        
        y_pos += 60
        
        # Close Debug button
        close_dev_button_rect = pygame.Rect(left_x + (total_width - 250) // 2, y_pos, 250, button_height)
        close_dev_button = UIWidgets.draw_button(
            self.screen,
            close_dev_button_rect,
            "Close Debug",
            self.font_small,
            is_primary=False
        )
        result['close_dev_button'] = close_dev_button
        
        y_pos += 60
