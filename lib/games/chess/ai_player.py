#!/usr/bin/env python3
"""
Computer Player (Stockfish AI)

Beheert computer tegenstander functionaliteit met visuele thinking feedback.
Uitgesloten uit chessgui.py voor betere code organisatie.

Functionaliteit:
- Asynchrone Stockfish move berekening (background thread)
- Visual "thinking" animation met pulserende dots tijdens berekening
- Thread-safe communicatie tussen AI en GUI
- Automatic move execution na berekening

Threading architectuur:
- Main thread: GUI rendering + animation @ 30 FPS
- Background thread: Stockfish berekening (blocking)
- Synchronisatie: thinking_done flag + 100ms polling interval

Animation:
- 300x120 semi-transparant overlay in center screen
- "Computer denkt na" tekst + 3 pulserende dots
- Smooth animation tijdens wait tijd

Architectuur:
Deze module is OPZETTELIJK gescheiden van stockfish.py:
- stockfish.py = Pure UCI engine interface (blocking, geen GUI)
- computer_player.py = GUI-specifieke wrapper (threading + pygame animaties)

Waarom gescheiden?
1. Stockfish.get_best_move() is blocking (duurt 1+ seconde)
2. Pygame GUI moet responsive blijven (30 FPS updates)
3. Oplossing: Threading + visual feedback (deze module)
4. Stockfish.py blijft herbruikbaar zonder pygame dependency

Hoofdklasse:
- ComputerPlayer: Encapsulates AI logic + visualization

Wordt gebruikt door: chessgame.py (bij vs_computer mode)
"""

import pygame
import chess
import threading


class ComputerPlayer:
    """Handles computer moves met Stockfish en visual feedback"""
    
    def __init__(self, stockfish, engine, gui, screen):
        """
        Args:
            stockfish: Stockfish engine instance
            engine: ChessEngine instance
            gui: ChessGUI instance
            screen: Pygame screen surface
        """
        self.stockfish = stockfish
        self.engine = engine
        self.gui = gui
        self.screen = screen
    
    def make_move(self):
        """Laat computer (Stockfish) een zet doen met thinking animatie"""
        print("\nComputer denkt...")
        
        # Threading voor non-blocking Stockfish
        thinking_done = False
        best_move = None
        
        def get_stockfish_move():
            nonlocal best_move, thinking_done
            # Haal think_time uit settings (gui heeft settings object)
            think_time = self.gui.settings.get('stockfish_think_time', 1000, section='chess') if hasattr(self.gui, 'settings') else 1000
            best_move = self.stockfish.get_best_move(self.engine.board, think_time_ms=think_time)
            thinking_done = True
        
        # Start Stockfish in aparte thread
        stockfish_thread = threading.Thread(target=get_stockfish_move)
        stockfish_thread.start()
        
        # Toon animatie terwijl we wachten
        clock = pygame.time.Clock()
        animation_frame = 0
        
        while not thinking_done:
            # Handle pygame events om freeze te voorkomen
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    thinking_done = True
                    break
            
            # Herteken GUI met thinking indicator
            self.screen.fill(self.gui.COLOR_BG)
            self.gui.draw_board()
            self.gui.draw_pieces()
            self.gui.draw_debug_overlays()
            if self.gui.settings.get('show_coordinates', True, section='debug'):
                self.gui.draw_coordinates()
            self.gui.draw_sidebar()
            
            # Teken "thinking" overlay
            self._draw_thinking_indicator(animation_frame)
            
            pygame.display.flip()
            animation_frame += 1
            clock.tick(30)  # 30 FPS voor smooth animatie
        
        # Wacht tot thread klaar is
        stockfish_thread.join()
        
        if best_move:
            from_square = chess.square_name(best_move.from_square)
            to_square = chess.square_name(best_move.to_square)
            
            print(f"Computer zet: {from_square} -> {to_square}")
            
            # Maak de zet
            self.engine.board.push(best_move)
            
            # Check game status
            if self.engine.is_game_over():
                print(f"\n*** {self.engine.get_game_result()} ***\n")
    
    def _draw_thinking_indicator(self, frame):
        """Teken thinking indicator overlay met pulserende dots"""
        # Grote overlay in het midden van het bord
        board_width = 800
        overlay_width = 300
        overlay_height = 120
        overlay_x = (board_width - overlay_width) // 2
        overlay_y = 300
        
        # Achtergrond box (solid, geen alpha)
        pygame.draw.rect(self.screen, (40, 40, 40), 
                        (overlay_x, overlay_y, overlay_width, overlay_height), 
                        border_radius=15)
        
        # Border (dikker en helderder)
        pygame.draw.rect(self.screen, (100, 200, 255), 
                        (overlay_x, overlay_y, overlay_width, overlay_height), 5, border_radius=15)
        
        # "Thinking..." tekst (groter)
        font = pygame.font.Font(None, 36)
        text = font.render("Computer thinking...", True, (255, 255, 255))
        text_rect = text.get_rect(center=(overlay_x + overlay_width // 2, overlay_y + 40))
        self.screen.blit(text, text_rect)
        
        # Rotating spinner (3 grotere dots die pulsen)
        dot_y = overlay_y + 80
        dot_spacing = 30
        center_x = overlay_x + overlay_width // 2
        
        for i in range(3):
            dot_x = center_x - dot_spacing + (i * dot_spacing)
            # Pulserende grootte gebaseerd op frame
            pulse = abs(((frame + i * 10) % 60) - 30) / 30.0  # 0.0 to 1.0
            radius = int(6 + pulse * 6)  # 6 tot 12 pixels
            
            # Teken dot (solid color, geen alpha)
            color_intensity = int(100 + pulse * 155)
            pygame.draw.circle(self.screen, (color_intensity, color_intensity, 255), (dot_x, dot_y), radius)
