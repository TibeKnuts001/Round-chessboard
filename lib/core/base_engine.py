#!/usr/bin/env python3
"""
Base Engine Interface

Abstract base class voor game engines.
Definieert de interface die alle game engines moeten implementeren.

Voor chess: Wrapper rond python-chess library
Voor checkers: Eigen checkers logic implementatie

Verplichte methods:
- reset(): Reset game naar start positie
- get_piece_at(position): Geef stuk op positie
- get_legal_moves_from(position): Legal moves vanaf positie
- make_move(from_pos, to_pos): Voer zet uit
- is_game_over(): Check of spel afgelopen is
- get_game_result(): Geef resultaat van spel
"""

from abc import ABC, abstractmethod


class BaseEngine(ABC):
    """Abstract base class voor game engines"""
    
    @abstractmethod
    def reset(self):
        """Reset game naar start positie"""
        pass
    
    @abstractmethod
    def get_piece_at(self, position):
        """
        Geef stuk op positie
        
        Args:
            position: Positie notatie (bijv. 'E4' voor chess, '12' voor checkers)
            
        Returns:
            Piece object of None
        """
        pass
    
    @abstractmethod
    def get_legal_moves_from(self, position):
        """
        Geef alle legale zetten vanaf een positie
        
        Args:
            position: Positie notatie
            
        Returns:
            List van posities waar naartoe gezet kan worden
        """
        pass
    
    @abstractmethod
    def make_move(self, from_pos, to_pos):
        """
        Voer zet uit
        
        Args:
            from_pos: Van positie
            to_pos: Naar positie
            
        Returns:
            True als zet geldig was, False anders
        """
        pass
    
    @abstractmethod
    def is_game_over(self):
        """
        Check of spel afgelopen is
        
        Returns:
            Boolean
        """
        pass
    
    @abstractmethod
    def get_game_result(self):
        """
        Geef resultaat van spel
        
        Returns:
            String met resultaat (bijv. "Checkmate!", "White wins!", etc.)
        """
        pass
