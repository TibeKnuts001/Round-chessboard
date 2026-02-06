#!/usr/bin/env python3
"""
Checkers Game - American Checkers / English Draughts

Gebruikt de gedeelde architectuur:
- BaseGame voor shared game loop logic
- CheckersEngine voor checkers-specifieke rules (py-draughts)
- CheckersGUI voor checkers-specifieke rendering
- Hardware (LEDs, sensors) gedeeld met chess

Dit toont hoe de refactoring werkt:
- checkersgame.py staat NAAST chessgame.py
- Beide hergebruiken lib/core/ (BaseGame, hardware, settings, GUI infrastructure)
- Elk heeft eigen lib/games/{game}/ voor game-specifieke code
"""

from lib.core.base_game import BaseGame
from lib.games.checkers import CheckersEngine, CheckersGUI, CheckersAIEngine


class CheckersGame(BaseGame):
    """Checkers game met sensor integratie - erft van BaseGame"""
    
    def _create_engine(self):
        """Maak checkers engine"""
        return CheckersEngine()
    
    def _create_gui(self, engine):
        """Maak checkers GUI"""
        return CheckersGUI(engine)
    
    def _is_vs_computer_enabled(self):
        """Check of VS Computer mode aan staat voor checkers"""
        vs_comp = self.gui.settings.get('play_vs_computer', False, section='checkers')
        return vs_comp
    
    def _create_ai(self):
        """Maak AI als VS Computer enabled is"""
        # Check of we in checkers sectie zitten (niet chess)
        if not self._is_vs_computer_enabled():
            return None
        
        print("Initializing Checkers AI...")
        difficulty = self.gui.settings.get('ai_difficulty', 5, section='checkers')
        think_time = self.gui.settings.get('ai_think_time', 1000, section='checkers')
        ai_engine = CheckersAIEngine(difficulty=difficulty, think_time=think_time)
        
        return ai_engine
    
    def make_computer_move(self):
        """Laat AI een zet doen"""
        if not self.ai:
            print("WARNING: make_computer_move called but no AI available")
            return
        
        print("\nAI denkt...")
        
        # Haal beste zet op van AI
        # AlphaBetaEngine gebruikt alleen depth, geen think_time
        best_move = self.ai.get_best_move(self.engine.board)
        
        if best_move:
            # Voer zet uit
            try:
                self.engine.board.push(best_move)
                self.engine.move_count += 1  # Track move count
                print(f"AI speelt: {best_move}")
            except Exception as e:
                print(f"Fout bij AI zet: {e}")
        else:
            print("AI kon geen zet vinden")


def main():
    """Start checkers game"""
    from lib.settings import Settings
    settings = Settings()
    brightness_percent = settings.get('brightness', 20)
    brightness_value = int((brightness_percent / 100) * 255)
    brightness_value = max(0, min(255, brightness_value))
    game = CheckersGame(brightness=brightness_value)
    game.run()


if __name__ == '__main__':
    main()
