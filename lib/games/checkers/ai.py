#!/usr/bin/env python3
"""
Checkers AI Engine Wrapper

Python interface naar een eenvoudige checkers AI.
Gebruikt voor computer tegenstander functionaliteit in checkers.

Functionaliteit:
- Best move berekening voor gegeven positie
- Difficulty level configuratie
- Support voor Amerikaanse dammen (8x8)

Engine details:
- Eenvoudige heuristiek-based engine (geen py-draughts AlphaBeta vanwege bugs)
- Evalueert materiaal en positionele factors
- Configureerbare depth

Hoofdklasse:
- CheckersAIEngine: Eenvoudige AI engine voor checkers

Wordt gebruikt door: CheckersGame (AI move generation)
"""

import random


class CheckersAIEngine:
    """Eenvoudige AI engine voor American Checkers"""
    
    def __init__(self, difficulty=5, think_time=1000):
        """
        Initialiseer Checkers AI engine
        
        Args:
            difficulty: Moeilijkheidsgraad 1-10 (1=zwakst, 10=sterkst)
            think_time: Denktijd in milliseconden (niet gebruikt)
        """
        self.difficulty = max(1, min(10, difficulty))
        self.think_time = think_time
        print(f"DEBUG: CheckersAI initialized with difficulty={difficulty} (heuristic engine)")
    
    def evaluate_position(self, board):
        """
        Evalueer bordpositie simpel
        
        Returns:
            Score (positief = goed voor huidige speler)
        """
        # Tel stukken (simpele materiaal evaluatie)
        pos = board.position
        
        # Men: -1 = white man, 1 = black man
        # Kings: -2 = white king, 2 = black king
        white_men = (pos == -1).sum()
        white_kings = (pos == -2).sum()
        black_men = (pos == 1).sum()
        black_kings = (pos == 2).sum()
        
        # Material score (king = 2.5 x man)
        white_score = white_men + white_kings * 2.5
        black_score = black_men + black_kings * 2.5
        
        # Return score for current player
        from draughts import Color
        if board.turn == Color.WHITE:
            return white_score - black_score
        else:
            return black_score - white_score
    
    def get_best_move(self, board):
        """
        Bereken beste zet voor huidige positie
        
        Args:
            board: py-draughts AmericanBoard object
            
        Returns:
            py-draughts Move object of None als geen zet mogelijk
        """
        try:
            legal_moves = list(board.legal_moves)
            
            if not legal_moves:
                return None
            
            # Difficulty 1-3: Random met voorkeur voor captures
            if self.difficulty <= 3:
                captures = [m for m in legal_moves if m.captured_list]
                if captures:
                    return random.choice(captures)
                return random.choice(legal_moves)
            
            # Difficulty 4-10: Evalueer zetten
            best_move = None
            best_score = -999999
            
            for move in legal_moves:
                # Probeer zet
                board.push(move)
                
                # Evalueer positie
                score = -self.evaluate_position(board)
                
                # Bonus voor captures
                if move.captured_list:
                    score += len(move.captured_list) * 100
                
                # Kleine random factor voor variatie
                score += random.random() * (11 - self.difficulty)
                
                # Neem zet terug
                board.pop()
                
                if score > best_score:
                    best_score = score
                    best_move = move
            
            return best_move
            
        except Exception as e:
            print(f"ERROR: CheckersAI.get_best_move() failed: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: random legal move
            legal_moves = list(board.legal_moves)
            return random.choice(legal_moves) if legal_moves else None
    
    def quit(self):
        """Stop engine (niet nodig maar voor compatibility)"""
        pass
    
    def set_difficulty(self, difficulty):
        """
        Pas moeilijkheidsgraad aan
        
        Args:
            difficulty: Nieuwe difficulty (1-10)
        """
        self.difficulty = max(1, min(10, difficulty))
        print(f"Difficulty aangepast naar {self.difficulty}")
    
    def set_think_time(self, think_time_ms):
        """
        Pas denktijd aan
        
        Args:
            think_time_ms: Denktijd in milliseconden (niet gebruikt)
        """
        self.think_time = think_time_ms
        print(f"Denktijd aangepast naar {self.think_time}ms")
        print(f"Denktijd aangepast naar {self.think_time}ms (info only, AlphaBetaEngine gebruikt depth)")

