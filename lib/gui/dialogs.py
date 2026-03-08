#!/usr/bin/env python3
"""
Confirmation Dialogs

Beheert popup dialogs voor gebruikersconfirmatie.
Voorkómt onbedoelde acties zoals afsluiten of nieuw spel starten.

Dialogs:
1. Exit Confirmation
   - Vraagt bevestiging voor app sluiten
   - Knoppen: "Ja" (quit) / "Nee" (cancel)
   - Triggered door: Quit button in sidebar

2. New Game Confirmation  
   - Vraagt bevestiging voor huidige spel resetten
   - Knoppen: "Ja" (reset) / "Nee" (cancel)
   - Triggered door: New Game button in sidebar

Visueel design:
- 400x200 pixel centered dialog box
- Semi-transparant overlay achter dialog (dim effect)
- Vraag tekst bovenaan (28pt font)
- Twee knoppen onderaan: Ja (grijs) / Nee (grijs)
- Hover effect: knoppen kleuren lichter bij mouseover

Hoofdklasse:
- DialogRenderer: Static methods voor dialog rendering + hit detection

Wordt gebruikt door: ChessGUI (via EventHandlers)
"""

import os
import pygame


class DialogRenderer:
    """Helper class voor het tekenen van confirmation dialogs"""
    
    # Kleuren (gedeeld met main GUI)
    COLOR_WHITE = (255, 255, 255)
    COLOR_BLACK = (0, 0, 0)
    COLOR_BUTTON = (70, 130, 180)
    COLOR_BUTTON_HOVER = (100, 149, 237)
    
    def __init__(self, screen, screen_width, screen_height, font, font_small):
        """
        Args:
            screen: Pygame screen surface
            screen_width: Screen width
            screen_height: Screen height
            font: Main font
            font_small: Small font
        """
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = font
        self.font_small = font_small
    
    def _draw_overlay(self):
        """Teken semi-transparante overlay"""
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
    def draw_exit_confirm_dialog(self):
        """
        Teken exit confirmation dialog
        
        Returns:
            Tuple: (yes_button, no_button)
        """
        self._draw_overlay()
        
        # Dialog box
        dialog_width = 400
        dialog_height = 200
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(self.screen, self.COLOR_WHITE, dialog_rect, border_radius=15)
        
        # Title
        title = self.font.render("Exit Game?", True, self.COLOR_BLACK)
        title_rect = title.get_rect(center=(self.screen_width // 2, dialog_y + 50))
        self.screen.blit(title, title_rect)
        
        # Message
        message = self.font_small.render("Are you sure you want to quit?", True, (100, 100, 100))
        message_rect = message.get_rect(center=(self.screen_width // 2, dialog_y + 90))
        self.screen.blit(message, message_rect)
        
        # Yes button (red)
        yes_button = pygame.Rect(
            self.screen_width // 2 - 160,
            dialog_y + dialog_height - 70,
            130,
            50
        )
        
        # No button (blue)
        no_button = pygame.Rect(
            self.screen_width // 2 + 30,
            dialog_y + dialog_height - 70,
            130,
            50
        )
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Yes button
        yes_color = (220, 70, 70) if yes_button.collidepoint(mouse_pos) else (200, 50, 50)
        pygame.draw.rect(self.screen, yes_color, yes_button, border_radius=10)
        yes_text = self.font.render("Yes", True, self.COLOR_WHITE)
        yes_text_rect = yes_text.get_rect(center=yes_button.center)
        self.screen.blit(yes_text, yes_text_rect)
        
        # No button
        no_color = self.COLOR_BUTTON_HOVER if no_button.collidepoint(mouse_pos) else self.COLOR_BUTTON
        pygame.draw.rect(self.screen, no_color, no_button, border_radius=10)
        no_text = self.font.render("No", True, self.COLOR_WHITE)
        no_text_rect = no_text.get_rect(center=no_button.center)
        self.screen.blit(no_text, no_text_rect)
        
        return yes_button, no_button
    
    def draw_new_game_confirm_dialog(self):
        """
        Teken new game confirmation dialog met 3 opties
        
        Returns:
            Tuple: (normal_button, assisted_button, cancel_button)
        """
        self._draw_overlay()
        
        # Dialog box (compacter voor 3 knoppen)
        dialog_width = 500
        dialog_height = 180
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(self.screen, self.COLOR_WHITE, dialog_rect, border_radius=15)
        
        # Title
        title = self.font.render("New Game?", True, self.COLOR_BLACK)
        title_rect = title.get_rect(center=(self.screen_width // 2, dialog_y + 35))
        self.screen.blit(title, title_rect)
        
        # Message
        message = self.font_small.render("Choose setup method:", True, (100, 100, 100))
        message_rect = message.get_rect(center=(self.screen_width // 2, dialog_y + 65))
        self.screen.blit(message, message_rect)
        
        # Normal button (groen)
        normal_button = pygame.Rect(
            self.screen_width // 2 - 220,
            dialog_y + dialog_height - 65,
            130,
            50
        )
        
        # Assisted button (blauw)
        assisted_button = pygame.Rect(
            self.screen_width // 2 - 65,
            dialog_y + dialog_height - 65,
            130,
            50
        )
        
        # Cancel button (grijs)
        cancel_button = pygame.Rect(
            self.screen_width // 2 + 90,
            dialog_y + dialog_height - 65,
            130,
            50
        )
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Normal button (groen)
        normal_color = (60, 180, 60) if normal_button.collidepoint(mouse_pos) else (50, 150, 50)
        pygame.draw.rect(self.screen, normal_color, normal_button, border_radius=10)
        normal_text = self.font_small.render("Normal", True, self.COLOR_WHITE)
        normal_text_rect = normal_text.get_rect(center=normal_button.center)
        self.screen.blit(normal_text, normal_text_rect)
        
        # Assisted button (blauw)
        assisted_color = (100, 149, 237) if assisted_button.collidepoint(mouse_pos) else (70, 130, 180)
        pygame.draw.rect(self.screen, assisted_color, assisted_button, border_radius=10)
        assisted_text = self.font_small.render("Assisted", True, self.COLOR_WHITE)
        assisted_text_rect = assisted_text.get_rect(center=assisted_button.center)
        self.screen.blit(assisted_text, assisted_text_rect)
        
        # Cancel button (grijs)
        cancel_color = (140, 140, 140) if cancel_button.collidepoint(mouse_pos) else (100, 100, 100)
        pygame.draw.rect(self.screen, cancel_color, cancel_button, border_radius=10)
        cancel_text = self.font_small.render("Cancel", True, self.COLOR_WHITE)
        cancel_text_rect = cancel_text.get_rect(center=cancel_button.center)
        self.screen.blit(cancel_text, cancel_text_rect)
        
        return normal_button, assisted_button, cancel_button
    
    def draw_skip_setup_step_dialog(self):
        """
        Teken skip setup step confirmation dialog
        
        Returns:
            Tuple: (yes_button, no_button, cancel_button)
        """
        self._draw_overlay()
        
        # Dialog box
        dialog_width = 500
        dialog_height = 230
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(self.screen, self.COLOR_WHITE, dialog_rect, border_radius=15)
        
        # Title
        title = self.font.render("Skip This Step?", True, self.COLOR_BLACK)
        title_rect = title.get_rect(center=(self.screen_width // 2, dialog_y + 45))
        self.screen.blit(title, title_rect)
        
        # Message line 1
        message1 = self.font_small.render("Not all pieces have been detected.", True, (100, 100, 100))
        message1_rect = message1.get_rect(center=(self.screen_width // 2, dialog_y + 85))
        self.screen.blit(message1, message1_rect)
        
        # Message line 2
        message2 = self.font_small.render("Continue to next step anyway?", True, (100, 100, 100))
        message2_rect = message2.get_rect(center=(self.screen_width // 2, dialog_y + 110))
        self.screen.blit(message2, message2_rect)
        
        # Three buttons: Skip, Wait, Cancel
        yes_button = pygame.Rect(
            self.screen_width // 2 - 220,
            dialog_y + dialog_height - 70,
            120,
            50
        )
        
        no_button = pygame.Rect(
            self.screen_width // 2 - 60,
            dialog_y + dialog_height - 70,
            120,
            50
        )
        
        cancel_button = pygame.Rect(
            self.screen_width // 2 + 100,
            dialog_y + dialog_height - 70,
            120,
            50
        )
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Skip button (orange/warning)
        yes_color = (240, 150, 60) if yes_button.collidepoint(mouse_pos) else (220, 130, 40)
        pygame.draw.rect(self.screen, yes_color, yes_button, border_radius=10)
        yes_text = self.font.render("Skip", True, self.COLOR_WHITE)
        yes_text_rect = yes_text.get_rect(center=yes_button.center)
        self.screen.blit(yes_text, yes_text_rect)
        
        # Wait button (blue)
        no_color = self.COLOR_BUTTON_HOVER if no_button.collidepoint(mouse_pos) else self.COLOR_BUTTON
        pygame.draw.rect(self.screen, no_color, no_button, border_radius=10)
        no_text = self.font.render("Wait", True, self.COLOR_WHITE)
        no_text_rect = no_text.get_rect(center=no_button.center)
        self.screen.blit(no_text, no_text_rect)
        
        # Cancel button (red)
        cancel_color = (220, 60, 60) if cancel_button.collidepoint(mouse_pos) else (180, 50, 50)
        pygame.draw.rect(self.screen, cancel_color, cancel_button, border_radius=10)
        cancel_text = self.font.render("Cancel", True, self.COLOR_WHITE)
        cancel_text_rect = cancel_text.get_rect(center=cancel_button.center)
        self.screen.blit(cancel_text, cancel_text_rect)
        
        return yes_button, no_button, cancel_button
    
    def draw_color_selection_dialog(self, white_on_left=True, computer_plays=None):
        """
        Teken color/side selection dialog voor start van nieuw spel.
        
        Args:
            white_on_left: True = wit links, False = zwart links
            computer_plays: 'white', 'black' of None (AI uit)
        
        Returns:
            Tuple: (swap_button, confirm_button, cancel_button,
                    computer_black_button, computer_off_button, computer_white_button)
        """
        self._draw_overlay()
        
        dialog_height = 390
        dialog_width = 520
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(self.screen, self.COLOR_WHITE, dialog_rect, border_radius=15)
        
        # Title
        title = self.font.render("Choose Sides", True, self.COLOR_BLACK)
        title_rect = title.get_rect(center=(self.screen_width // 2, dialog_y + 32))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.font_small.render("Wie speelt welke kant van het bord?", True, (100, 100, 100))
        subtitle_rect = subtitle.get_rect(center=(self.screen_width // 2, dialog_y + 60))
        self.screen.blit(subtitle, subtitle_rect)
        
        # --- Color panels ---
        panel_w = 155
        panel_h = 100
        panel_y = dialog_y + 85
        left_panel_x = dialog_x + 40
        right_panel_x = dialog_x + dialog_width - 40 - panel_w
        
        mouse_pos = pygame.mouse.get_pos()
        
        if white_on_left:
            left_color, left_label, left_text_color = (240, 240, 240), "Wit", (30, 30, 30)
            right_color, right_label, right_text_color = (30, 30, 30), "Zwart", (220, 220, 220)
        else:
            left_color, left_label, left_text_color = (30, 30, 30), "Zwart", (220, 220, 220)
            right_color, right_label, right_text_color = (240, 240, 240), "Wit", (30, 30, 30)
        
        # Left panel
        left_panel_rect = pygame.Rect(left_panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(self.screen, left_color, left_panel_rect, border_radius=12)
        pygame.draw.rect(self.screen, (180, 180, 180), left_panel_rect, 2, border_radius=12)
        left_label_surf = self.font.render(left_label, True, left_text_color)
        left_label_rect = left_label_surf.get_rect(center=left_panel_rect.center)
        self.screen.blit(left_label_surf, left_label_rect)
        
        left_sub = self.font_small.render("Links", True, (130, 130, 130))
        self.screen.blit(left_sub, (left_panel_x + (panel_w - left_sub.get_width()) // 2, panel_y + panel_h + 6))
        
        # Right panel
        right_panel_rect = pygame.Rect(right_panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(self.screen, right_color, right_panel_rect, border_radius=12)
        pygame.draw.rect(self.screen, (180, 180, 180), right_panel_rect, 2, border_radius=12)
        right_label_surf = self.font.render(right_label, True, right_text_color)
        right_label_rect = right_label_surf.get_rect(center=right_panel_rect.center)
        self.screen.blit(right_label_surf, right_label_rect)
        
        right_sub = self.font_small.render("Rechts", True, (130, 130, 130))
        self.screen.blit(right_sub, (right_panel_x + (panel_w - right_sub.get_width()) // 2, panel_y + panel_h + 6))
        
        # Swap button (center)
        swap_cx = self.screen_width // 2
        swap_cy = panel_y + panel_h // 2
        swap_button = pygame.Rect(swap_cx - 30, swap_cy - 22, 60, 44)
        swap_hover = swap_button.collidepoint(mouse_pos)
        swap_bg = (100, 160, 230) if swap_hover else (70, 130, 200)
        pygame.draw.rect(self.screen, swap_bg, swap_button, border_radius=10)
        # Laad switch icon (eenmalig, gecached op instance)
        if not hasattr(self, '_switch_icon'):
            icon_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'assets', 'switch.png'
            )
            try:
                raw = pygame.image.load(icon_path).convert_alpha()
                icon_size = min(swap_button.width - 10, swap_button.height - 10)
                self._switch_icon = pygame.transform.smoothscale(raw, (icon_size, icon_size))
            except Exception:
                self._switch_icon = None
        if self._switch_icon:
            icon_r = self._switch_icon.get_rect(center=swap_button.center)
            self.screen.blit(self._switch_icon, icon_r)
        else:
            swap_label = self.font_small.render("< >", True, (255, 255, 255))
            self.screen.blit(swap_label, swap_label.get_rect(center=swap_button.center))
        
        # --- AI 3-positie schakelaar (altijd zichtbaar) ---
        ai_section_y = panel_y + panel_h + 42
        ai_label = self.font_small.render("AI Tegenstander:", True, self.COLOR_BLACK)
        self.screen.blit(ai_label, ai_label.get_rect(center=(self.screen_width // 2, ai_section_y)))
        
        toggle_w = 360
        toggle_h = 46
        toggle_x = (self.screen_width - toggle_w) // 2
        toggle_y = ai_section_y + 26
        seg_w = toggle_w // 3
        
        # Track achtergrond
        track_rect = pygame.Rect(toggle_x, toggle_y, toggle_w, toggle_h)
        pygame.draw.rect(self.screen, (210, 210, 210), track_rect, border_radius=23)
        
        # 3 klikbare segmenten: Wit | Uit | Zwart (zelfde volgorde als kleurpanelen boven)
        computer_white_button = pygame.Rect(toggle_x,              toggle_y, seg_w,                toggle_h)
        computer_off_button   = pygame.Rect(toggle_x + seg_w,      toggle_y, seg_w,                toggle_h)
        computer_black_button = pygame.Rect(toggle_x + seg_w * 2,  toggle_y, toggle_w - seg_w * 2, toggle_h)
        
        # Actief segment en kleuren
        if computer_plays == 'white':
            active_btn   = computer_white_button
            pill_color   = (200, 200, 200)
            label_colors = [(30, 30, 30), (80, 80, 80), (80, 80, 80)]
        elif computer_plays == 'black':
            active_btn   = computer_black_button
            pill_color   = (40, 40, 40)
            label_colors = [(80, 80, 80), (80, 80, 80), (255, 255, 255)]
        else:  # None = Uit
            active_btn   = computer_off_button
            pill_color   = (110, 110, 110)
            label_colors = [(80, 80, 80), (255, 255, 255), (80, 80, 80)]
        
        # Teken actieve pill (iets kleiner dan segment)
        pill_rect = pygame.Rect(active_btn.x + 3, active_btn.y + 3,
                                active_btn.width - 6, active_btn.height - 6)
        pygame.draw.rect(self.screen, pill_color, pill_rect, border_radius=20)
        
        # Labels
        for btn, lbl, txt_col in zip(
            [computer_white_button, computer_off_button, computer_black_button],
            ["Wit", "Uit", "Zwart"],
            label_colors
        ):
            txt = self.font_small.render(lbl, True, txt_col)
            self.screen.blit(txt, txt.get_rect(center=btn.center))
        
        # --- Confirm / Cancel buttons ---
        confirm_button = pygame.Rect(
            self.screen_width // 2 - 150,
            dialog_y + dialog_height - 65,
            130,
            50
        )
        cancel_button = pygame.Rect(
            self.screen_width // 2 + 20,
            dialog_y + dialog_height - 65,
            130,
            50
        )
        
        confirm_color = (60, 180, 60) if confirm_button.collidepoint(mouse_pos) else (50, 150, 50)
        pygame.draw.rect(self.screen, confirm_color, confirm_button, border_radius=10)
        confirm_text = self.font_small.render("Bevestigen", True, self.COLOR_WHITE)
        self.screen.blit(confirm_text, confirm_text.get_rect(center=confirm_button.center))
        
        cancel_color = (140, 140, 140) if cancel_button.collidepoint(mouse_pos) else (100, 100, 100)
        pygame.draw.rect(self.screen, cancel_color, cancel_button, border_radius=10)
        cancel_text = self.font_small.render("Annuleren", True, self.COLOR_WHITE)
        self.screen.blit(cancel_text, cancel_text.get_rect(center=cancel_button.center))
        
        return (swap_button, confirm_button, cancel_button,
                computer_black_button, computer_off_button, computer_white_button)
    
    def draw_stop_game_confirm_dialog(self):
        """
        Teken stop game confirmation dialog
        
        Returns:
            Tuple: (yes_button, no_button)
        """
        self._draw_overlay()
        
        # Dialog box
        dialog_width = 400
        dialog_height = 200
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(self.screen, self.COLOR_WHITE, dialog_rect, border_radius=15)
        
        # Title
        title = self.font.render("Stop Game?", True, self.COLOR_BLACK)
        title_rect = title.get_rect(center=(self.screen_width // 2, dialog_y + 50))
        self.screen.blit(title, title_rect)
        
        # Message
        message = self.font_small.render("Stop current game and reset the board?", True, (100, 100, 100))
        message_rect = message.get_rect(center=(self.screen_width // 2, dialog_y + 90))
        self.screen.blit(message, message_rect)
        
        # Yes button (red for danger action)
        yes_button = pygame.Rect(
            self.screen_width // 2 - 160,
            dialog_y + dialog_height - 70,
            130,
            50
        )
        
        # No button (blue to cancel)
        no_button = pygame.Rect(
            self.screen_width // 2 + 30,
            dialog_y + dialog_height - 70,
            130,
            50
        )
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Yes button (red)
        yes_color = (230, 70, 70) if yes_button.collidepoint(mouse_pos) else (200, 50, 50)
        pygame.draw.rect(self.screen, yes_color, yes_button, border_radius=10)
        yes_text = self.font.render("Yes", True, self.COLOR_WHITE)
        yes_text_rect = yes_text.get_rect(center=yes_button.center)
        self.screen.blit(yes_text, yes_text_rect)
        
        # No button
        no_color = self.COLOR_BUTTON_HOVER if no_button.collidepoint(mouse_pos) else self.COLOR_BUTTON
        pygame.draw.rect(self.screen, no_color, no_button, border_radius=10)
        no_text = self.font.render("No", True, self.COLOR_WHITE)
        no_text_rect = no_text.get_rect(center=no_button.center)
        self.screen.blit(no_text, no_text_rect)
        
        return yes_button, no_button
    
    def draw_undo_confirm_dialog(self):
        """
        Teken undo confirmation dialog
        
        Returns:
            Tuple: (yes_button, no_button)
        """
        self._draw_overlay()
        
        # Dialog box
        dialog_width = 400
        dialog_height = 200
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(self.screen, self.COLOR_WHITE, dialog_rect, border_radius=15)
        
        # Title
        title = self.font.render("Undo Move?", True, self.COLOR_BLACK)
        title_rect = title.get_rect(center=(self.screen_width // 2, dialog_y + 50))
        self.screen.blit(title, title_rect)
        
        # Message
        message = self.font_small.render("Undo the last move(s)?", True, (100, 100, 100))
        message_rect = message.get_rect(center=(self.screen_width // 2, dialog_y + 90))
        self.screen.blit(message, message_rect)
        
        # Yes button
        yes_button = pygame.Rect(
            self.screen_width // 2 - 160,
            dialog_y + dialog_height - 70,
            130,
            50
        )
        
        # No button
        no_button = pygame.Rect(
            self.screen_width // 2 + 30,
            dialog_y + dialog_height - 70,
            130,
            50
        )
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Yes button
        yes_color = self.COLOR_BUTTON_HOVER if yes_button.collidepoint(mouse_pos) else self.COLOR_BUTTON
        pygame.draw.rect(self.screen, yes_color, yes_button, border_radius=10)
        yes_text = self.font.render("Yes", True, self.COLOR_WHITE)
        yes_text_rect = yes_text.get_rect(center=yes_button.center)
        self.screen.blit(yes_text, yes_text_rect)
        
        # No button
        no_color = (180, 180, 180) if no_button.collidepoint(mouse_pos) else (150, 150, 150)
        pygame.draw.rect(self.screen, no_color, no_button, border_radius=10)
        no_text = self.font.render("No", True, self.COLOR_WHITE)
        no_text_rect = no_text.get_rect(center=no_button.center)
        self.screen.blit(no_text, no_text_rect)
        
        return yes_button, no_button
    
    def draw_update_status_dialog(self, update_info):
        """
        Teken update status dialog
        
        Args:
            update_info: Dict met keys:
                - 'status': 'checking', 'up_to_date', 'available', 'success', 'error'
                - 'message': str met status bericht
                - 'details': optional list van detail regels
        
        Returns:
            ok_button rect (alleen voor success/error/up_to_date)
        """
        self._draw_overlay()
        
        status = update_info.get('status', 'checking')
        message = update_info.get('message', 'Checking for updates...')
        details = update_info.get('details', [])
        
        # Dialog dimensions (groter voor meer info)
        dialog_width = 500
        dialog_height = 250 + (len(details) * 25)
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(self.screen, self.COLOR_WHITE, dialog_rect, border_radius=15)
        
        # Title based on status
        title_text = {
            'checking': 'Checking Updates...',
            'up_to_date': 'Up to Date',
            'available': 'Update Available',
            'success': 'Update Successful!',
            'error': 'Update Failed'
        }.get(status, 'Update Status')
        
        title = self.font.render(title_text, True, self.COLOR_BLACK)
        title_rect = title.get_rect(center=(self.screen_width // 2, dialog_y + 40))
        self.screen.blit(title, title_rect)
        
        # Main message
        y_pos = dialog_y + 90
        message_text = self.font_small.render(message, True, (60, 60, 60))
        message_rect = message_text.get_rect(center=(self.screen_width // 2, y_pos))
        self.screen.blit(message_text, message_rect)
        
        # Details
        y_pos += 40
        for detail in details:
            detail_text = self.font_small.render(detail, True, (100, 100, 100))
            detail_rect = detail_text.get_rect(center=(self.screen_width // 2, y_pos))
            self.screen.blit(detail_text, detail_rect)
            y_pos += 25
        
        # Buttons based on status
        if status == 'available':
            # Two buttons: Update and Cancel
            button_y = dialog_y + dialog_height - 70
            
            # Update button (left)
            update_button = pygame.Rect(
                self.screen_width // 2 - 140,
                button_y,
                120,
                50
            )
            
            # Cancel button (right)
            cancel_button = pygame.Rect(
                self.screen_width // 2 + 20,
                button_y,
                120,
                50
            )
            
            mouse_pos = pygame.mouse.get_pos()
            
            # Draw Update button
            update_color = self.COLOR_BUTTON_HOVER if update_button.collidepoint(mouse_pos) else self.COLOR_BUTTON
            pygame.draw.rect(self.screen, update_color, update_button, border_radius=10)
            update_text = self.font.render("Update", True, self.COLOR_WHITE)
            update_text_rect = update_text.get_rect(center=update_button.center)
            self.screen.blit(update_text, update_text_rect)
            
            # Draw Cancel button
            cancel_color = (150, 150, 150) if cancel_button.collidepoint(mouse_pos) else (120, 120, 120)
            pygame.draw.rect(self.screen, cancel_color, cancel_button, border_radius=10)
            cancel_text = self.font.render("Cancel", True, self.COLOR_WHITE)
            cancel_text_rect = cancel_text.get_rect(center=cancel_button.center)
            self.screen.blit(cancel_text, cancel_text_rect)
            
            return {'update_button': update_button, 'cancel_button': cancel_button}
        
        elif status in ['up_to_date', 'success', 'error']:
            # Single OK button
            ok_button = pygame.Rect(
                self.screen_width // 2 - 65,
                dialog_y + dialog_height - 70,
                130,
                50
            )
            
            mouse_pos = pygame.mouse.get_pos()
            button_color = self.COLOR_BUTTON_HOVER if ok_button.collidepoint(mouse_pos) else self.COLOR_BUTTON
            pygame.draw.rect(self.screen, button_color, ok_button, border_radius=10)
            
            ok_text = self.font.render("OK", True, self.COLOR_WHITE)
            ok_text_rect = ok_text.get_rect(center=ok_button.center)
            self.screen.blit(ok_text, ok_text_rect)
            
            return {'ok_button': ok_button}
        
        return None
