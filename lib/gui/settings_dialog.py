#!/usr/bin/env python3
"""
Settings Dialog

Volledige settings interface met tabbladen voor verschillende configuraties.
Gebruikt temp_settings pattern: wijzigingen worden pas opgeslagen bij OK.

Tabs:
1. General
   - VS Computer toggle (speel tegen Stockfish)
   - LED Brightness slider (0-100%)

2. Stockfish (alleen zichtbaar als VS Computer aan)
   - Skill Level slider (0-20)
   - Think Time slider (500-5000 ms)
   - Search Depth slider (5-25)
   - Threads slider (1-4)

3. Debug
   - Show Coordinates toggle (toon A-H/1-8 labels)
   - Show Sensor Detection toggle (debug overlay)
   - Info text over debug mode gebruik

Temp Settings Pattern:
- Bij openen: kopie settings naar temp_settings dict
- Tijdens editing: wijzigingen alleen in temp_settings
- Bij OK: kopieer temp_settings → settings, save(), clear temp
- Bij ESC/Cancel: clear temp_settings, wijzigingen verloren

Visueel:
- 600x500 pixel dialog centered on screen
- Tab buttons bovenaan (General / Stockfish / Debug)
- Content area met toggles en sliders
- OK knop onderaan (slaat op + sluit)

Hoofdklasse:
- SettingsDialog: Rendering + layout logic voor settings UI

Wordt gebruikt door: ChessGUI + EventHandlers
"""

import pygame


class SettingsDialog:
    """Settings dialog renderer met tabs"""
    
    # Kleuren (gedeeld met main GUI)
    COLOR_WHITE = (255, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    COLOR_BUTTON = (70, 130, 180)
    COLOR_BUTTON_HOVER = (100, 149, 237)
    
    def __init__(self, screen, screen_width, screen_height, font, font_small, gui=None):
        """
        Args:
            screen: Pygame screen surface
            screen_width: Screen width
            screen_height: Screen height
            font: Main font
            font_small: Small font
            gui: Reference to ChessGUI instance (for dropdown state)
        """
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = font
        self.font_small = font_small
        self.gui = gui  # Store GUI reference
    
    def _draw_overlay(self):
        """Teken semi-transparante overlay"""
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
    
    def draw(self, settings, active_tab):
        """
        Teken settings dialog met tabs
        
        Returns:
            Dict met alle interactive rects: {
                'ok_button': rect,
                'tabs': {'general': rect, 'stockfish': rect, 'gameplay': rect, 'debug': rect},
                'sliders': {'brightness': rect, 'skill': rect, 'think_time': rect, 'depth': rect, 'threads': rect},
                'toggles': {'coordinates': rect, 'debug_sensors': rect, 'vs_computer': rect, 'strict_touch_move': rect, 'validate_board_state': rect}
            }
        """
        self._draw_overlay()
        
        # Dialog box
        dialog_width = 600
        dialog_height = 450
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(self.screen, self.COLOR_WHITE, dialog_rect, border_radius=15)
        
        # Title
        title = self.font.render("Settings", True, self.COLOR_BLACK)
        title_rect = title.get_rect(center=(self.screen_width // 2, dialog_y + 30))
        self.screen.blit(title, title_rect)
        
        # Tabs (4 tabs nu)
        tab_y = dialog_y + 60
        tab_width = 100
        tab_height = 40
        tab_spacing = 10
        
        general_tab = pygame.Rect(dialog_x + 50, tab_y, tab_width, tab_height)
        stockfish_tab = pygame.Rect(dialog_x + 50 + tab_width + tab_spacing, tab_y, tab_width, tab_height)
        gameplay_tab = pygame.Rect(dialog_x + 50 + 2 * (tab_width + tab_spacing), tab_y, tab_width, tab_height)
        debug_tab = pygame.Rect(dialog_x + 50 + 3 * (tab_width + tab_spacing), tab_y, tab_width, tab_height)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Draw General tab
        general_color = (70, 130, 180) if active_tab == 'general' else (150, 150, 150)
        if general_tab.collidepoint(mouse_pos) and active_tab != 'general':
            general_color = (100, 149, 237)
        pygame.draw.rect(self.screen, general_color, general_tab, border_radius=8)
        general_text = self.font_small.render("General", True, self.COLOR_WHITE)
        general_text_rect = general_text.get_rect(center=general_tab.center)
        self.screen.blit(general_text, general_text_rect)
        
        # Draw Stockfish tab (alleen als VS Computer aan staat)
        stockfish_enabled = settings.get('play_vs_computer', False)
        if stockfish_enabled:
            stockfish_color = (70, 130, 180) if active_tab == 'stockfish' else (150, 150, 150)
            if stockfish_tab.collidepoint(mouse_pos) and active_tab != 'stockfish':
                stockfish_color = (100, 149, 237)
            pygame.draw.rect(self.screen, stockfish_color, stockfish_tab, border_radius=8)
            stockfish_text = self.font_small.render("Stockfish", True, self.COLOR_WHITE)
            stockfish_text_rect = stockfish_text.get_rect(center=stockfish_tab.center)
            self.screen.blit(stockfish_text, stockfish_text_rect)
        else:
            # Disabled appearance
            pygame.draw.rect(self.screen, (100, 100, 100), stockfish_tab, border_radius=8)
            stockfish_text = self.font_small.render("Stockfish", True, (180, 180, 180))
            stockfish_text_rect = stockfish_text.get_rect(center=stockfish_tab.center)
            self.screen.blit(stockfish_text, stockfish_text_rect)
        
        # Draw Gameplay tab
        gameplay_color = (70, 130, 180) if active_tab == 'gameplay' else (150, 150, 150)
        if gameplay_tab.collidepoint(mouse_pos) and active_tab != 'gameplay':
            gameplay_color = (100, 149, 237)
        pygame.draw.rect(self.screen, gameplay_color, gameplay_tab, border_radius=8)
        gameplay_text = self.font_small.render("Gameplay", True, self.COLOR_WHITE)
        gameplay_text_rect = gameplay_text.get_rect(center=gameplay_tab.center)
        self.screen.blit(gameplay_text, gameplay_text_rect)
        
        # Draw Debug tab
        debug_color = (70, 130, 180) if active_tab == 'debug' else (150, 150, 150)
        if debug_tab.collidepoint(mouse_pos) and active_tab != 'debug':
            debug_color = (100, 149, 237)
        pygame.draw.rect(self.screen, debug_color, debug_tab, border_radius=8)
        debug_text = self.font_small.render("Debug", True, self.COLOR_WHITE)
        debug_text_rect = debug_text.get_rect(center=debug_tab.center)
        self.screen.blit(debug_text, debug_text_rect)
        
        # Content area
        content_y = tab_y + tab_height + 20
        
        # Draw content based on active tab
        result = {
            'ok_button': None,
            'tabs': {'general': general_tab, 'stockfish': stockfish_tab if stockfish_enabled else None, 'gameplay': gameplay_tab, 'debug': debug_tab},
            'sliders': {},
            'toggles': {}
        }
        
        if active_tab == 'general':
            self._draw_general_tab(dialog_x, content_y, settings, result)
        elif active_tab == 'stockfish' and stockfish_enabled:
            self._draw_stockfish_tab(dialog_x, content_y, settings, result)
        elif active_tab == 'gameplay':
            self._draw_gameplay_tab(dialog_x, content_y, settings, result)
        elif active_tab == 'debug':
            self._draw_debug_tab(dialog_x, content_y, settings, result)
        
        # OK button (draw FIRST)
        ok_button = pygame.Rect(
            self.screen_width // 2 - 75,
            dialog_y + dialog_height - 70,
            150,
            50
        )
        
        button_color = self.COLOR_BUTTON_HOVER if ok_button.collidepoint(mouse_pos) else self.COLOR_BUTTON
        pygame.draw.rect(self.screen, button_color, ok_button, border_radius=10)
        
        ok_text = self.font.render("OK", True, self.COLOR_WHITE)
        ok_text_rect = ok_text.get_rect(center=ok_button.center)
        self.screen.blit(ok_text, ok_text_rect)
        
        result['ok_button'] = ok_button
        
        # Draw dropdown list items AFTER OK button so dropdown is on top
        if result.get('dropdown_items'):
            for val, item_rect, text, is_selected in result['dropdown_items']:
                # Highlight if selected
                if is_selected:
                    pygame.draw.rect(self.screen, (200, 220, 255), item_rect)
                else:
                    pygame.draw.rect(self.screen, (250, 250, 250), item_rect)
                
                # Border
                pygame.draw.rect(self.screen, (180, 180, 180), item_rect, width=1)
                
                # Text
                item_text = self.font_small.render(text, True, self.COLOR_BLACK)
                self.screen.blit(item_text, (item_rect.x + 10, item_rect.y + 8))
        
        return result
    
    def _draw_general_tab(self, dialog_x, content_y, settings, result):
        """Teken general tab content"""
        y_pos = content_y
        
        toggle_width = 80
        toggle_height = 40
        toggle_x = dialog_x + 50
        
        # VS Computer toggle
        vs_computer_toggle_rect = pygame.Rect(toggle_x, y_pos, toggle_width, toggle_height)
        
        # Bepaal kleuren op basis van setting
        vs_computer_on = settings.get('play_vs_computer', False)
        vs_computer_bg_color = (76, 175, 80) if vs_computer_on else (158, 158, 158)
        
        # Teken achtergrond (rounded rectangle)
        slider_radius = toggle_height // 2 - 4
        pygame.draw.rect(self.screen, vs_computer_bg_color, vs_computer_toggle_rect, border_radius=toggle_height // 2)
        
        # Teken slider knop (cirkel)
        vs_computer_slider_x = toggle_x + toggle_width - slider_radius - 4 if vs_computer_on else toggle_x + slider_radius + 4
        vs_computer_slider_center = (vs_computer_slider_x, y_pos + toggle_height // 2)
        pygame.draw.circle(self.screen, self.COLOR_WHITE, vs_computer_slider_center, slider_radius)
        
        # Label
        vs_computer_label = self.font_small.render("Play vs Computer (Stockfish)", True, self.COLOR_BLACK)
        self.screen.blit(vs_computer_label, (vs_computer_toggle_rect.right + 15, y_pos + 8))
        
        y_pos += 80
        
        # Power Profile dropdown
        label_width = 140
        dropdown_width = 300
        dropdown_height = 40
        label_x = dialog_x + 30
        dropdown_x = label_x + label_width + 20
        dropdown_y = y_pos  # Bewaar voor dropdown lijst positie
        
        power_label = self.font_small.render("Power Profile", True, self.COLOR_BLACK)
        self.screen.blit(power_label, (label_x, y_pos + 8))
        
        # Power profile opties
        power_profiles = [
            (0.5, "0.5A (Low Power)"),
            (1.0, "1.0A (Medium)"),
            (1.5, "1.5A (Standard)"),
            (2.0, "2.0A (High)"),
            (2.5, "2.5A (Maximum)")
        ]
        
        current_power = settings.get('power_profile', 1.5)
        current_text = next((text for val, text in power_profiles if val == current_power), "1.5A (Standard)")
        
        # Dropdown achtergrond (main button)
        dropdown_rect = pygame.Rect(dropdown_x, y_pos, dropdown_width, dropdown_height)
        pygame.draw.rect(self.screen, (230, 230, 230), dropdown_rect, border_radius=8)
        pygame.draw.rect(self.screen, (180, 180, 180), dropdown_rect, width=2, border_radius=8)
        
        # Tekst
        dropdown_text = self.font_small.render(current_text, True, self.COLOR_BLACK)
        self.screen.blit(dropdown_text, (dropdown_x + 10, y_pos + 10))
        
        # Pijltje (naar beneden of boven afhankelijk van open/dicht)
        arrow_size = 8
        arrow_x = dropdown_x + dropdown_width - 20
        arrow_y = y_pos + dropdown_height // 2
        
        # Import gui object from result dict to check dropdown state
        from lib.chessgui import ChessGUI
        # We need access to the GUI instance - we'll pass it via settings_dialog
        # For now, check if dropdown should be open via a flag we'll add
        
        if hasattr(self, 'gui') and self.gui.show_power_dropdown:
            # Pijltje omhoog (dropdown is open)
            arrow_points = [
                (arrow_x, arrow_y + 4),
                (arrow_x + arrow_size, arrow_y + 4),
                (arrow_x + arrow_size // 2, arrow_y - 4)
            ]
        else:
            # Pijltje naar beneden (dropdown is dicht)
            arrow_points = [
                (arrow_x, arrow_y - 4),
                (arrow_x + arrow_size, arrow_y - 4),
                (arrow_x + arrow_size // 2, arrow_y + 4)
            ]
        pygame.draw.polygon(self.screen, self.COLOR_BLACK, arrow_points)
        
        y_pos += 70
        
        # LED Brightness slider (teken dit VOOR de dropdown lijst zodat lijst er overheen komt)
        slider_width = 300
        slider_height = 8
        slider_x = label_x + label_width + 20  # 20px spacing
        knob_radius = 18
        interaction_height = 40
        
        slider_label = self.font_small.render("LED Brightness", True, self.COLOR_BLACK)
        self.screen.blit(slider_label, (label_x, y_pos + 8))
        
        # Get max brightness from power profile
        from lib.settings import Settings
        max_brightness = Settings.POWER_PROFILES.get(current_power, 60)
        
        # Slider track
        track_y = y_pos + (interaction_height - slider_height) // 2
        slider_rect = pygame.Rect(slider_x, track_y, slider_width, slider_height)
        pygame.draw.rect(self.screen, (200, 200, 200), slider_rect, border_radius=4)
        
        # Slider fill
        brightness = min(settings.get('brightness', 20), max_brightness)  # Cap at power profile max
        fill_width = int((brightness / 100) * slider_width)
        fill_rect = pygame.Rect(slider_x, track_y, fill_width, slider_height)
        pygame.draw.rect(self.screen, (76, 175, 80), fill_rect, border_radius=4)
        
        # Slider knob
        knob_x = slider_x + fill_width
        knob_y = track_y + slider_height // 2
        
        # Shadow
        pygame.draw.circle(self.screen, (100, 100, 100), (knob_x + 2, knob_y + 2), knob_radius)
        pygame.draw.circle(self.screen, (76, 175, 80), (knob_x, knob_y), knob_radius)
        pygame.draw.circle(self.screen, self.COLOR_WHITE, (knob_x, knob_y), knob_radius - 4)
        
        # Interaction area
        brightness_slider_rect = pygame.Rect(slider_x - knob_radius, y_pos, slider_width + 2 * knob_radius, interaction_height)
        
        # Brightness percentage
        brightness_text = self.font_small.render(f"{brightness}%", True, self.COLOR_BLACK)
        self.screen.blit(brightness_text, (slider_x + slider_width + 10, y_pos + 8))
        
        # Store dropdown items info for later rendering
        dropdown_items = []
        if hasattr(self, 'gui') and self.gui.show_power_dropdown:
            item_height = 35
            list_y = dropdown_y + dropdown_height
            
            for i, (val, text) in enumerate(power_profiles):
                item_rect = pygame.Rect(dropdown_x, list_y + i * item_height, dropdown_width, item_height)
                is_selected = (val == current_power)
                dropdown_items.append((val, item_rect, text, is_selected))
        
        # Update result dict
        result['toggles']['vs_computer'] = vs_computer_toggle_rect
        result['dropdowns'] = result.get('dropdowns', {})
        result['dropdowns']['power_profile'] = dropdown_rect
        result['dropdown_items'] = dropdown_items  # List van (value, rect) tuples
        result['sliders']['brightness'] = brightness_slider_rect
        result['power_profiles'] = power_profiles
        result['max_brightness'] = max_brightness

    
    def _draw_stockfish_tab(self, dialog_x, content_y, settings, result):
        """Teken Stockfish tab content"""
        y_pos = content_y + 20
        
        label_width = 140
        slider_width = 300
        slider_height = 8
        label_x = dialog_x + 30
        slider_x = label_x + label_width + 20  # 20px spacing between label and slider
        knob_radius = 18
        interaction_height = 40
        
        # Skill Level slider (0-20)
        skill_label = self.font_small.render("Skill Level", True, self.COLOR_BLACK)
        self.screen.blit(skill_label, (label_x, y_pos + 8))
        
        track_y = y_pos + (interaction_height - slider_height) // 2
        skill_track = pygame.Rect(slider_x, track_y, slider_width, slider_height)
        pygame.draw.rect(self.screen, (200, 200, 200), skill_track, border_radius=4)
        
        skill_level = settings.get('stockfish_skill_level', 10)
        skill_fill_width = int((skill_level / 20) * slider_width)
        skill_fill = pygame.Rect(slider_x, track_y, skill_fill_width, slider_height)
        pygame.draw.rect(self.screen, (255, 165, 0), skill_fill, border_radius=4)
        
        skill_knob_x = slider_x + skill_fill_width
        skill_knob_y = track_y + slider_height // 2
        pygame.draw.circle(self.screen, (100, 100, 100), (skill_knob_x + 2, skill_knob_y + 2), knob_radius)
        pygame.draw.circle(self.screen, (255, 165, 0), (skill_knob_x, skill_knob_y), knob_radius)
        pygame.draw.circle(self.screen, self.COLOR_WHITE, (skill_knob_x, skill_knob_y), knob_radius - 4)
        
        skill_slider_rect = pygame.Rect(slider_x - knob_radius, y_pos, slider_width + 2 * knob_radius, interaction_height)
        
        difficulty_labels = ["Beginner", "Easy", "Medium", "Hard", "Expert"]
        difficulty_idx = min(4, skill_level // 5)
        skill_text = self.font_small.render(f"{skill_level}/20 ({difficulty_labels[difficulty_idx]})", True, self.COLOR_BLACK)
        self.screen.blit(skill_text, (slider_x + slider_width + 10, y_pos + 8))
        
        y_pos += 50
        
        # Think Time slider (500-5000 ms)
        think_label = self.font_small.render("Think Time (ms)", True, self.COLOR_BLACK)
        self.screen.blit(think_label, (label_x, y_pos + 8))
        
        track_y = y_pos + (interaction_height - slider_height) // 2
        think_track = pygame.Rect(slider_x, track_y, slider_width, slider_height)
        pygame.draw.rect(self.screen, (200, 200, 200), think_track, border_radius=4)
        
        think_time = settings.get('stockfish_think_time', 1000)
        think_fill_width = int(((think_time - 500) / 4500) * slider_width)
        think_fill = pygame.Rect(slider_x, track_y, think_fill_width, slider_height)
        pygame.draw.rect(self.screen, (100, 149, 237), think_fill, border_radius=4)
        
        think_knob_x = slider_x + think_fill_width
        think_knob_y = track_y + slider_height // 2
        pygame.draw.circle(self.screen, (100, 100, 100), (think_knob_x + 2, think_knob_y + 2), knob_radius)
        pygame.draw.circle(self.screen, (100, 149, 237), (think_knob_x, think_knob_y), knob_radius)
        pygame.draw.circle(self.screen, self.COLOR_WHITE, (think_knob_x, think_knob_y), knob_radius - 4)
        
        think_slider_rect = pygame.Rect(slider_x - knob_radius, y_pos, slider_width + 2 * knob_radius, interaction_height)
        
        think_text = self.font_small.render(f"{think_time} ms", True, self.COLOR_BLACK)
        self.screen.blit(think_text, (slider_x + slider_width + 10, y_pos + 8))
        
        y_pos += 50
        
        # Search Depth slider (5-25)
        depth_label = self.font_small.render("Search Depth", True, self.COLOR_BLACK)
        self.screen.blit(depth_label, (label_x, y_pos + 8))
        
        track_y = y_pos + (interaction_height - slider_height) // 2
        depth_track = pygame.Rect(slider_x, track_y, slider_width, slider_height)
        pygame.draw.rect(self.screen, (200, 200, 200), depth_track, border_radius=4)
        
        depth = settings.get('stockfish_depth', 15)
        depth_fill_width = int(((depth - 5) / 20) * slider_width)
        depth_fill = pygame.Rect(slider_x, track_y, depth_fill_width, slider_height)
        pygame.draw.rect(self.screen, (156, 39, 176), depth_fill, border_radius=4)
        
        depth_knob_x = slider_x + depth_fill_width
        depth_knob_y = track_y + slider_height // 2
        pygame.draw.circle(self.screen, (100, 100, 100), (depth_knob_x + 2, depth_knob_y + 2), knob_radius)
        pygame.draw.circle(self.screen, (156, 39, 176), (depth_knob_x, depth_knob_y), knob_radius)
        pygame.draw.circle(self.screen, self.COLOR_WHITE, (depth_knob_x, depth_knob_y), knob_radius - 4)
        
        depth_slider_rect = pygame.Rect(slider_x - knob_radius, y_pos, slider_width + 2 * knob_radius, interaction_height)
        
        depth_text = self.font_small.render(f"{depth}", True, self.COLOR_BLACK)
        self.screen.blit(depth_text, (slider_x + slider_width + 10, y_pos + 8))
        
        y_pos += 50
        
        # Threads slider (1-4)
        threads_label = self.font_small.render("Threads", True, self.COLOR_BLACK)
        self.screen.blit(threads_label, (label_x, y_pos + 8))
        
        track_y = y_pos + (interaction_height - slider_height) // 2
        threads_track = pygame.Rect(slider_x, track_y, slider_width, slider_height)
        pygame.draw.rect(self.screen, (200, 200, 200), threads_track, border_radius=4)
        
        threads = settings.get('stockfish_threads', 1)
        threads_fill_width = int(((threads - 1) / 3) * slider_width)
        threads_fill = pygame.Rect(slider_x, track_y, threads_fill_width, slider_height)
        pygame.draw.rect(self.screen, (255, 87, 34), threads_fill, border_radius=4)
        
        threads_knob_x = slider_x + threads_fill_width
        threads_knob_y = track_y + slider_height // 2
        pygame.draw.circle(self.screen, (100, 100, 100), (threads_knob_x + 2, threads_knob_y + 2), knob_radius)
        pygame.draw.circle(self.screen, (255, 87, 34), (threads_knob_x, threads_knob_y), knob_radius)
        pygame.draw.circle(self.screen, self.COLOR_WHITE, (threads_knob_x, threads_knob_y), knob_radius - 4)
        
        threads_slider_rect = pygame.Rect(slider_x - knob_radius, y_pos, slider_width + 2 * knob_radius, interaction_height)
        
        threads_text = self.font_small.render(f"{threads}", True, self.COLOR_BLACK)
        self.screen.blit(threads_text, (slider_x + slider_width + 10, y_pos + 8))
        
        # Update result dict
        result['sliders']['skill'] = skill_slider_rect
        result['sliders']['think_time'] = think_slider_rect
        result['sliders']['depth'] = depth_slider_rect
        result['sliders']['threads'] = threads_slider_rect
    
    def _draw_gameplay_tab(self, dialog_x, content_y, settings, result):
        """Teken gameplay tab content"""
        y_pos = content_y + 20
        
        toggle_width = 80
        toggle_height = 40
        toggle_x = dialog_x + 50
        slider_radius = toggle_height // 2 - 4
        
        # Strict touch-move toggle
        touch_move_toggle_rect = pygame.Rect(toggle_x, y_pos, toggle_width, toggle_height)
        
        # Bepaal kleuren op basis van setting
        is_on = settings.get('strict_touch_move', False)
        bg_color = (76, 175, 80) if is_on else (158, 158, 158)
        
        # Teken achtergrond (rounded rectangle)
        pygame.draw.rect(self.screen, bg_color, touch_move_toggle_rect, border_radius=toggle_height // 2)
        
        # Teken slider knop (cirkel)
        slider_x = toggle_x + toggle_width - slider_radius - 4 if is_on else toggle_x + slider_radius + 4
        slider_center = (slider_x, y_pos + toggle_height // 2)
        pygame.draw.circle(self.screen, self.COLOR_WHITE, slider_center, slider_radius)
        
        # Label
        label = self.font_small.render("Strict Touch-Move Rule", True, self.COLOR_BLACK)
        self.screen.blit(label, (touch_move_toggle_rect.right + 15, y_pos + 8))
        
        # Info text for touch-move
        y_pos += 60
        info_text = self.font_small.render("Strict = must move touched piece", True, (100, 100, 100))
        self.screen.blit(info_text, (dialog_x + 50, y_pos))
        
        # Update result dict
        result['toggles']['strict_touch_move'] = touch_move_toggle_rect
    
    def _draw_debug_tab(self, dialog_x, content_y, settings, result):
        """Teken debug tab content"""
        y_pos = content_y
        
        toggle_width = 80
        toggle_height = 40
        toggle_x = dialog_x + 50
        slider_radius = toggle_height // 2 - 4
        
        # Show coordinates toggle
        toggle_rect = pygame.Rect(toggle_x, y_pos, toggle_width, toggle_height)
        
        # Bepaal kleuren op basis van setting
        is_on = settings.get('show_coordinates', True)
        bg_color = (76, 175, 80) if is_on else (158, 158, 158)
        
        # Teken achtergrond (rounded rectangle)
        pygame.draw.rect(self.screen, bg_color, toggle_rect, border_radius=toggle_height // 2)
        
        # Teken slider knop (cirkel)
        slider_x = toggle_x + toggle_width - slider_radius - 4 if is_on else toggle_x + slider_radius + 4
        slider_center = (slider_x, y_pos + toggle_height // 2)
        pygame.draw.circle(self.screen, self.COLOR_WHITE, slider_center, slider_radius)
        
        # Label
        label = self.font_small.render("Show coordinates (A-H, 1-8)", True, self.COLOR_BLACK)
        self.screen.blit(label, (toggle_rect.right + 15, y_pos + 8))
        
        y_pos += 80
        
        # Debug sensors toggle
        debug_toggle_rect = pygame.Rect(toggle_x, y_pos, toggle_width, toggle_height)
        
        is_on = settings.get('debug_sensors', False)
        bg_color = (76, 175, 80) if is_on else (158, 158, 158)
        
        pygame.draw.rect(self.screen, bg_color, debug_toggle_rect, border_radius=toggle_height // 2)
        
        slider_x = toggle_x + toggle_width - slider_radius - 4 if is_on else toggle_x + slider_radius + 4
        slider_center = (slider_x, y_pos + toggle_height // 2)
        pygame.draw.circle(self.screen, self.COLOR_WHITE, slider_center, slider_radius)
        
        label = self.font_small.render("Show sensor detection (yellow M)", True, self.COLOR_BLACK)
        self.screen.blit(label, (debug_toggle_rect.right + 15, y_pos + 8))
        
        y_pos += 80
        
        # Board validation toggle
        validate_toggle_rect = pygame.Rect(toggle_x, y_pos, toggle_width, toggle_height)
        
        is_on = settings.get('validate_board_state', True)
        bg_color = (76, 175, 80) if is_on else (158, 158, 158)
        
        pygame.draw.rect(self.screen, bg_color, validate_toggle_rect, border_radius=toggle_height // 2)
        
        slider_x = toggle_x + toggle_width - slider_radius - 4 if is_on else toggle_x + slider_radius + 4
        slider_center = (slider_x, y_pos + toggle_height // 2)
        pygame.draw.circle(self.screen, self.COLOR_WHITE, slider_center, slider_radius)
        
        label = self.font_small.render("Validate Board State", True, self.COLOR_BLACK)
        self.screen.blit(label, (validate_toggle_rect.right + 15, y_pos + 8))
        
        # Info text
        y_pos += 80
        info_lines = [
            "When enabled, yellow circles with 'M'",
            "(Magnet) appear in the center of squares",
            "where sensors detect a chess piece."
        ]
        for line in info_lines:
            info_text = self.font_small.render(line, True, (100, 100, 100))
            self.screen.blit(info_text, (dialog_x + 50, y_pos))
            y_pos += 25
        
        # Update result dict
        result['toggles']['coordinates'] = toggle_rect
        result['toggles']['debug_sensors'] = debug_toggle_rect
        result['toggles']['validate_board_state'] = validate_toggle_rect 