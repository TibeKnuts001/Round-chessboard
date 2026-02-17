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
