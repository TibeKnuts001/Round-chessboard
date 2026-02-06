#!/usr/bin/env python3
"""
Chess Game - Refactored versie met BaseGame

Gebruikt de nieuwe architectuur:
- BaseGame voor shared game loop logic
- ChessEngine voor chess-specifieke rules
- ChessGUI voor chess-specifieke rendering
- StockfishEngine voor AI
"""

import pygame
import chess
import threading
import time
from lib.core.base_game import BaseGame
from lib.games.chess import ChessEngine, ChessGUI, StockfishEngine


class ChessGame(BaseGame):
    """Chess game met sensor integratie - erft van BaseGame"""
    
    def _create_engine(self):
        """Maak chess engine"""
        return ChessEngine()
    
    def _create_gui(self, engine):
        """Maak chess GUI"""
        return ChessGUI(engine)
    
    def _is_strict_touch_move_enabled(self):
        """Check of strict touch-move aan staat voor chess"""
        return self.gui.settings.get('strict_touch_move', False, section='chess')
    
    def _create_ai(self):
        """Maak Stockfish AI als VS Computer enabled is"""
        skill = self.gui.settings.get('stockfish_skill_level', 10)
        threads = self.gui.settings.get('stockfish_threads', 1)
        depth = self.gui.settings.get('stockfish_depth', 15)
        stockfish = StockfishEngine(skill_level=skill, threads=threads, depth=depth)
        
        # Check of stockfish succesvol is gestart
        if stockfish and not stockfish.process:
            print("Stockfish kon niet starten - VS Computer mode uitgeschakeld")
            self.gui.settings.set('play_vs_computer', False)
            return None
        
        return stockfish
    
    def make_computer_move(self):
        """Laat Stockfish een zet doen"""
        if not self.ai:
            return
        
        print("\nComputer denkt...")
        
        # Threading voor async Stockfish berekening
        thinking_done = False
        best_move = None
        
        def get_stockfish_move():
            nonlocal best_move, thinking_done
            think_time = self.gui.settings.get('stockfish_think_time', 1000)
            best_move = self.ai.get_best_move(self.engine.board, think_time_ms=think_time)
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
            if self.gui.settings.get('show_coordinates', True):
                self.gui.draw_coordinates()
            self.gui.draw_sidebar()
            
            # Teken "thinking" overlay
            self._draw_thinking_indicator(animation_frame)
            
            pygame.display.flip()
            animation_frame += 1
            clock.tick(30)  # 30 FPS
        
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
        """Teken thinking indicator overlay"""
        board_width = 800
        overlay_width = 300
        overlay_height = 120
        overlay_x = (board_width - overlay_width) // 2
        overlay_y = 300
        
        # Achtergrond box
        pygame.draw.rect(self.screen, (40, 40, 40), 
                        (overlay_x, overlay_y, overlay_width, overlay_height), 
                        border_radius=15)
        
        # Border
        pygame.draw.rect(self.screen, (100, 200, 255), 
                        (overlay_x, overlay_y, overlay_width, overlay_height), 5, border_radius=15)
        
        # "Thinking..." tekst
        font = pygame.font.Font(None, 36)
        text = font.render("Computer thinking...", True, (255, 255, 255))
        text_rect = text.get_rect(center=(overlay_x + overlay_width // 2, overlay_y + 40))
        self.screen.blit(text, text_rect)
        
        # Rotating spinner (3 dots die pulsen)
        dot_y = overlay_y + 80
        dot_spacing = 30
        center_x = overlay_x + overlay_width // 2
        
        for i in range(3):
            dot_x = center_x - dot_spacing + (i * dot_spacing)
            pulse = abs(((frame + i * 10) % 60) - 30) / 30.0
            radius = int(6 + pulse * 6)
            
            color_intensity = int(100 + pulse * 155)
            pygame.draw.circle(self.screen, (color_intensity, color_intensity, 255), (dot_x, dot_y), radius)
    
    def _update_ai_status(self):
        """Update Stockfish status indien settings gewijzigd"""
        vs_computer_enabled = self.gui.settings.get('play_vs_computer', False)
        stockfish_skill = self.gui.settings.get('stockfish_skill_level', 10)
        stockfish_threads = self.gui.settings.get('stockfish_threads', 1)
        stockfish_depth = self.gui.settings.get('stockfish_depth', 15)
        
        if vs_computer_enabled and not self.ai:
            # Toon loading notification VOOR laden
            self.temp_message = ("Loading Stockfish engine...", "info")
            self.temp_message_timer = pygame.time.get_ticks() + 5000
            
            # Force een redraw om notification te tonen
            self.gui.draw(self.temp_message, self.temp_message_timer)
            pygame.display.flip()
            
            print(f"Starting Stockfish engine (skill {stockfish_skill}, threads {stockfish_threads}, depth {stockfish_depth})...")
            self.ai = self._create_ai()
            
            # Clear notification na laden
            self.temp_message = None
            
        elif not vs_computer_enabled and self.ai:
            print("Stopping Stockfish engine...")
            self.ai.cleanup()
            self.ai = None
        elif vs_computer_enabled and self.ai:
            # Update parameters als die veranderd zijn
            if hasattr(self.ai, 'skill_level') and self.ai.skill_level != stockfish_skill:
                print(f"Updating Stockfish skill level to {stockfish_skill}...")
                self.ai.skill_level = stockfish_skill
                self.ai._send_command(f"setoption name Skill Level value {stockfish_skill}")
            
            if hasattr(self.ai, 'threads') and self.ai.threads != stockfish_threads:
                print(f"Updating Stockfish threads to {stockfish_threads}...")
                self.ai.threads = stockfish_threads
                self.ai._send_command(f"setoption name Threads value {stockfish_threads}")
            
            if hasattr(self.ai, 'depth') and self.ai.depth != stockfish_depth:
                print(f"Updating Stockfish depth to {stockfish_depth}...")
                self.ai.depth = stockfish_depth


def main():
    """Start chess game"""
    from lib.settings import Settings
    settings = Settings()
    brightness_percent = settings.get('brightness', 20)
    brightness_value = int((brightness_percent / 100) * 255)
    brightness_value = max(0, min(255, brightness_value))
    game = ChessGame(brightness=brightness_value)
    game.run()


if __name__ == '__main__':
    main()
