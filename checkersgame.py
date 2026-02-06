#!/usr/bin/env python3
"""
Checkers Game - American Checkers / English Draughts

Gebruikt de gedeelde architectuur:
- BaseGame voor shared game loop logic
- CheckersEngine voor checkers-specifieke rules (pydraughts)
- CheckersGUI voor checkers-specifieke rendering
- Hardware (LEDs, sensors) gedeeld met chess

Dit toont hoe de refactoring werkt:
- checkersgame.py staat NAAST chessgame.py
- Beide hergebruiken lib/core/ (BaseGame, hardware, settings, GUI infrastructure)
- Elk heeft eigen lib/games/{game}/ voor game-specifieke code
"""

from lib.core.base_game import BaseGame
from lib.games.checkers import CheckersEngine, CheckersGUI


class CheckersGame(BaseGame):
    """Checkers game met sensor integratie - erft van BaseGame"""
    
    def _create_engine(self):
        """Maak checkers engine"""
        return CheckersEngine()
    
    def _create_gui(self, engine):
        """Maak checkers GUI"""
        return CheckersGUI(engine)
    
    def _create_ai(self):
        """Geen AI voor checkers (nog niet geïmplementeerd)"""
        return None
    
    def make_computer_move(self):
        """Checkers AI nog niet geïmplementeerd"""
        pass  # TODO: Implementeer checkers AI


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
