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
        Teken new game confirmation dialog
        
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
        title = self.font.render("New Game?", True, self.COLOR_BLACK)
        title_rect = title.get_rect(center=(self.screen_width // 2, dialog_y + 50))
        self.screen.blit(title, title_rect)
        
        # Message
        message = self.font_small.render("Start a new game and reset the board?", True, (100, 100, 100))
        message_rect = message.get_rect(center=(self.screen_width // 2, dialog_y + 90))
        self.screen.blit(message, message_rect)
        
        # Yes button (green)
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
        yes_color = (60, 180, 60) if yes_button.collidepoint(mouse_pos) else (50, 150, 50)
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
