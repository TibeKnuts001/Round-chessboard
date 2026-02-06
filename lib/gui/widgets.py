#!/usr/bin/env python3
"""
UI Widgets

Herbruikbare UI components voor alle dialogs en settings.
Bevat sliders, toggles, dropdowns, en andere interactive elements.
"""

import pygame


class UIWidgets:
    """Collection van herbruikbare UI widgets"""
    
    # Kleuren
    COLOR_WHITE = (255, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    COLOR_BUTTON = (70, 130, 180)
    COLOR_BUTTON_HOVER = (100, 149, 237)
    COLOR_TAB_ACTIVE = (70, 130, 180)
    COLOR_TAB_INACTIVE = (150, 150, 150)
    
    @staticmethod
    def draw_slider(screen, x, y, width, value, min_val, max_val, label_text, font_small):
        """
        Teken slider EXACT zoals origineel in settings_dialog.py
        
        Args:
            screen: Pygame surface
            x, y: Top-left van interaction area (40px hoog)
            width: Breedte van track (bijv. 300px)
            value: Huidige waarde
            min_val: Minimum waarde
            max_val: Maximum waarde
            label_text: Text rechts van slider (bijv. "50%" of "1000 ms")
            font_small: Font voor text
            
        Returns:
            pygame.Rect van interaction area (voor drag detection)
        """
        slider_height = 8
        knob_radius = 18
        interaction_height = 40
        
        # Track positie (gecentreerd verticaal in 40px interaction area)
        track_y = y + (interaction_height - slider_height) // 2
        
        # Track background (grijs)
        track_rect = pygame.Rect(x, track_y, width, slider_height)
        pygame.draw.rect(screen, (200, 200, 200), track_rect, border_radius=4)
        
        # Slider fill (groen)
        normalized = (value - min_val) / (max_val - min_val) if max_val > min_val else 0
        fill_width = int(normalized * width)
        fill_rect = pygame.Rect(x, track_y, fill_width, slider_height)
        pygame.draw.rect(screen, (76, 175, 80), fill_rect, border_radius=4)
        
        # Knob positie
        knob_x = x + fill_width
        knob_y = track_y + slider_height // 2
        
        # Knob shadow
        pygame.draw.circle(screen, (100, 100, 100), (knob_x + 2, knob_y + 2), knob_radius)
        # Knob outer circle (groen)
        pygame.draw.circle(screen, (76, 175, 80), (knob_x, knob_y), knob_radius)
        # Knob inner circle (wit)
        pygame.draw.circle(screen, UIWidgets.COLOR_WHITE, (knob_x, knob_y), knob_radius - 4)
        
        # Text rechts van slider (originele positie: y + 8)
        text_surface = font_small.render(label_text, True, UIWidgets.COLOR_BLACK)
        screen.blit(text_surface, (x + width + 10, y + 8))
        
        # Interaction area (inclusief knob overflow)
        interaction_rect = pygame.Rect(x - knob_radius, y, width + 2 * knob_radius, interaction_height)
        
        return interaction_rect
    
    @staticmethod
    def draw_toggle(screen, x, y, is_on, font_small=None):
        """
        Teken een toggle switch (ON/OFF)
        
        Args:
            screen: Pygame surface
            x, y: Positie linksboven
            is_on: Boolean state
            font_small: Optional font voor ON/OFF labels
            
        Returns:
            pygame.Rect van de toggle (voor click detection)
        """
        toggle_width = 80
        toggle_height = 40
        toggle_rect = pygame.Rect(x, y, toggle_width, toggle_height)
        
        # Background kleur
        bg_color = (76, 175, 80) if is_on else (158, 158, 158)
        pygame.draw.rect(screen, bg_color, toggle_rect, border_radius=toggle_height // 2)
        
        # Slider knop (cirkel)
        slider_radius = toggle_height // 2 - 4
        slider_x = x + toggle_width - slider_radius - 4 if is_on else x + slider_radius + 4
        slider_center = (slider_x, y + toggle_height // 2)
        pygame.draw.circle(screen, UIWidgets.COLOR_WHITE, slider_center, slider_radius)
        
        return toggle_rect
    
    @staticmethod
    def draw_dropdown(screen, x, y, width, height, selected_text, is_open, font_small):
        """
        Teken een dropdown button
        
        Args:
            screen: Pygame surface
            x, y: Positie linksboven
            width, height: Afmetingen
            selected_text: Huidige geselecteerde tekst
            is_open: Of dropdown lijst open is
            font_small: Font voor tekst
            
        Returns:
            pygame.Rect van de dropdown button
        """
        dropdown_rect = pygame.Rect(x, y, width, height)
        
        # Background
        pygame.draw.rect(screen, (230, 230, 230), dropdown_rect, border_radius=8)
        pygame.draw.rect(screen, (180, 180, 180), dropdown_rect, width=2, border_radius=8)
        
        # Text
        text = font_small.render(selected_text, True, UIWidgets.COLOR_BLACK)
        screen.blit(text, (x + 10, y + 10))
        
        # Arrow (up als open, down als closed)
        arrow_size = 8
        arrow_x = x + width - 20
        arrow_y = y + height // 2
        
        if is_open:
            # Pijl omhoog
            arrow_points = [
                (arrow_x, arrow_y + 4),
                (arrow_x + arrow_size, arrow_y + 4),
                (arrow_x + arrow_size // 2, arrow_y - 4)
            ]
        else:
            # Pijl naar beneden
            arrow_points = [
                (arrow_x, arrow_y - 4),
                (arrow_x + arrow_size, arrow_y - 4),
                (arrow_x + arrow_size // 2, arrow_y + 4)
            ]
        pygame.draw.polygon(screen, UIWidgets.COLOR_BLACK, arrow_points)
        
        return dropdown_rect
    
    @staticmethod
    def draw_dropdown_items(screen, x, y, width, item_height, items, selected_value, font_small):
        """
        Teken dropdown lijst items
        
        Args:
            screen: Pygame surface
            x, y: Positie linksboven van lijst
            width: Breedte van items
            item_height: Hoogte per item
            items: List van (value, display_text) tuples
            selected_value: Huidige geselecteerde waarde
            font_small: Font voor tekst
            
        Returns:
            List van (value, rect, text, is_selected) tuples
        """
        result = []
        
        for i, (value, text) in enumerate(items):
            item_y = y + i * item_height
            item_rect = pygame.Rect(x, item_y, width, item_height)
            is_selected = (value == selected_value)
            
            # Background
            if is_selected:
                pygame.draw.rect(screen, (200, 220, 255), item_rect)
            else:
                pygame.draw.rect(screen, (250, 250, 250), item_rect)
            
            # Border
            pygame.draw.rect(screen, (180, 180, 180), item_rect, width=1)
            
            # Text
            item_text = font_small.render(text, True, UIWidgets.COLOR_BLACK)
            screen.blit(item_text, (x + 10, item_y + 8))
            
            result.append((value, item_rect, text, is_selected))
        
        return result
    
    @staticmethod
    def draw_tab(screen, rect, label, is_active, is_enabled, font_small):
        """
        Teken een tab button
        
        Args:
            screen: Pygame surface
            rect: pygame.Rect voor tab positie
            label: Tab label tekst
            is_active: Of deze tab actief is
            is_enabled: Of deze tab clickbaar is
            font_small: Font voor label
            
        Returns:
            De rect (voor click detection)
        """
        mouse_pos = pygame.mouse.get_pos()
        
        # Bepaal kleur
        if not is_enabled:
            color = (100, 100, 100)
            text_color = (180, 180, 180)
        elif is_active:
            color = UIWidgets.COLOR_TAB_ACTIVE
            text_color = UIWidgets.COLOR_WHITE
        elif rect.collidepoint(mouse_pos):
            color = UIWidgets.COLOR_BUTTON_HOVER
            text_color = UIWidgets.COLOR_WHITE
        else:
            color = UIWidgets.COLOR_TAB_INACTIVE
            text_color = UIWidgets.COLOR_WHITE
        
        # Draw tab
        pygame.draw.rect(screen, color, rect, border_radius=8)
        
        # Draw text
        text = font_small.render(label, True, text_color)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)
        
        return rect
    
    @staticmethod
    def draw_button(screen, rect, label, font_small, is_primary=True, is_danger=False):
        """
        Teken een standaard button
        
        Args:
            screen: Pygame surface
            rect: pygame.Rect voor button positie
            label: Button tekst
            font_small: Font voor tekst
            is_primary: Of dit een primary button is (blauwe kleur)
            is_danger: Of dit een danger button is (rode kleur)
            
        Returns:
            De rect (voor click detection)
        """
        # Button kleur
        if is_danger:
            color = (200, 50, 50)  # Rood
        elif is_primary:
            color = UIWidgets.COLOR_BUTTON
        else:
            color = (150, 150, 150)
        
        # Hover effect
        mouse_pos = pygame.mouse.get_pos()
        if rect.collidepoint(mouse_pos):
            if is_danger:
                color = (230, 70, 70)  # Lichter rood bij hover
            elif is_primary:
                color = UIWidgets.COLOR_BUTTON_HOVER
            else:
                color = (180, 180, 180)
        
        # Draw button
        pygame.draw.rect(screen, color, rect, border_radius=8)
        
        # Draw text
        text = font_small.render(label, True, UIWidgets.COLOR_WHITE)
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)
        
        return rect

    @staticmethod
    def draw_notification(screen, message, board_width=800, board_height=800, notification_type='warning'):
        """
        Teken een notification overlay (gecentreerd op bord)
        
        Args:
            screen: Pygame surface
            message: Bericht tekst
            board_width: Breedte van het bord (voor centreren)
            board_height: Hoogte van het bord (voor centreren)
            notification_type: 'warning', 'error', 'info', 'success'
        """
        overlay_width = 400
        overlay_height = 100
        # Centreer in het midden van het 800x800 speelveld (links op scherm)
        overlay_x = (board_width - overlay_width) // 2  # Horizontaal gecentreerd in bord
        overlay_y = (board_height - overlay_height) // 2  # Verticaal gecentreerd in bord
        
        # Kleuren per type (simpele icons zonder unicode)
        if notification_type == 'error':
            bg_color = (120, 20, 20)
            border_color = (255, 50, 50)
            icon_color = (255, 100, 100)
            icon_text = "X"
        elif notification_type == 'success':
            bg_color = (20, 80, 20)
            border_color = (50, 200, 50)
            icon_color = (100, 255, 100)
            icon_text = "OK"
        elif notification_type == 'info':
            bg_color = (20, 60, 100)
            border_color = (50, 150, 255)
            icon_color = (100, 200, 255)
            icon_text = "i"
        else:  # warning (default)
            bg_color = (80, 40, 20)
            border_color = (255, 150, 0)
            icon_color = (255, 200, 0)
            icon_text = "!"
        
        # Achtergrond box met shadow voor depth
        shadow_offset = 4
        pygame.draw.rect(screen, (0, 0, 0, 100), 
                        (overlay_x + shadow_offset, overlay_y + shadow_offset, overlay_width, overlay_height), 
                        border_radius=12)
        
        # Achtergrond box
        pygame.draw.rect(screen, bg_color, 
                        (overlay_x, overlay_y, overlay_width, overlay_height), 
                        border_radius=12)
        
        # Border
        pygame.draw.rect(screen, border_color, 
                        (overlay_x, overlay_y, overlay_width, overlay_height), 4, border_radius=12)
        
        # Icon (simpele text, geen unicode)
        font_large = pygame.font.Font(None, 72)
        icon = font_large.render(icon_text, True, icon_color)
        icon_rect = icon.get_rect(center=(overlay_x + 40, overlay_y + overlay_height // 2))
        screen.blit(icon, icon_rect)
        
        # Message tekst
        font = pygame.font.Font(None, 28)
        text = font.render(message, True, UIWidgets.COLOR_WHITE)
        text_rect = text.get_rect(center=(overlay_x + overlay_width // 2 + 20, overlay_y + overlay_height // 2))
        screen.blit(text, text_rect)
