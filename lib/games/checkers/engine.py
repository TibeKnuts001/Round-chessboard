#!/usr/bin/env python3
"""
Checkers Engine Integration

Deze module beheert de damlogica via de pydraughts library.
Gebruikt Amerikaanse/Engelse dammen regels op 8x8 bord.

Functionaliteit:
- Board state management (positie van alle stukken)
- Legal move validation (controleert of zetten toegestaan zijn)
- Forced capture detection (verplichte slagen)
- King promotion (dammen)
- Game state detection (win/loss/draw)

Hoofdklasse:
- CheckersEngine: Wrapper rond pydraughts.Board met helper methods

Notatie:
- Velden zijn genummerd 1-32 (alleen de donkere vakken)
- Chess notatie mapping: A1-H8 -> 1-32 numbering
"""

from draughts import Board
from lib.core.base_engine import BaseEngine


class CheckersEngine(BaseEngine):
    """Wrapper voor pydraughts engine - Amerikaanse dammen (8x8)"""
    
    # Mapping van chess notatie (A1-H8) naar checkers square numbers (1-32)
    # Alleen donkere vakken worden gebruikt in dammen
    CHESS_TO_CHECKERS = {
        # Row 8 (top, zwart speelt vanaf boven)
        'B8': 1, 'D8': 2, 'F8': 3, 'H8': 4,
        # Row 7
        'A7': 5, 'C7': 6, 'E7': 7, 'G7': 8,
        # Row 6
        'B6': 9, 'D6': 10, 'F6': 11, 'H6': 12,
        # Row 5
        'A5': 13, 'C5': 14, 'E5': 15, 'G5': 16,
        # Row 4
        'B4': 17, 'D4': 18, 'F4': 19, 'H4': 20,
        # Row 3
        'A3': 21, 'C3': 22, 'E3': 23, 'G3': 24,
        # Row 2
        'B2': 25, 'D2': 26, 'F2': 27, 'H2': 28,
        # Row 1 (bottom, wit speelt vanaf onder)
        'A1': 29, 'C1': 30, 'E1': 31, 'G1': 32,
    }
    
    CHECKERS_TO_CHESS = {v: k for k, v in CHESS_TO_CHECKERS.items()}
    
    def __init__(self):
        """Initialiseer nieuw damspel in startpositie"""
        # Amerikaanse dammen (8x8, ook bekend als "English draughts")
        # Gebruik variant="english" voor 8x8 board met 32 vakken (nummering 1-32)
        self.board = Board(variant="english")
        self.selected_square = None
    
    def reset(self):
        """Reset bord naar startpositie"""
        self.board = Board(variant="english")
        self.selected_square = None
    
    def get_piece_at(self, chess_notation):
        """
        Geef stuk op positie
        
        Args:
            chess_notation: String zoals 'E3', 'A1', etc.
            
        Returns:
            Piece object (SimpleNamespace met .color en .is_king) of None
        """
        # Converteer chess notatie naar checkers square number
        square_num = self.CHESS_TO_CHECKERS.get(chess_notation.upper())
        if square_num is None:
            return None  # Licht vakje, geen stuk mogelijk
        
        # Check of er een stuk staat via FEN
        position = self.board.fen
        parts = position.split(':')
        
        # In pydraughts FEN: W = eerste speler (bovenaan = black), B = tweede speler (onderaan = white)
        first_player_pieces = []   # Bovenaan (black in ons spel)
        second_player_pieces = []  # Onderaan (white in ons spel)
        first_player_kings = []
        second_player_kings = []
        
        for part in parts:
            if part.startswith('W'):
                pieces_str = part[1:]
                if pieces_str:
                    for p in pieces_str.split(','):
                        if p.startswith('K'):
                            first_player_kings.append(int(p[1:]))
                        else:
                            first_player_pieces.append(int(p))
            elif part.startswith('B'):
                pieces_str = part[1:]
                if pieces_str:
                    for p in pieces_str.split(','):
                        if p.startswith('K'):
                            second_player_kings.append(int(p[1:]))
                        else:
                            second_player_pieces.append(int(p))
        
        # Check of ons square een stuk heeft
        from types import SimpleNamespace
        
        # W in FEN = bovenaan (squares 1-12) = black pieces in ons spel
        # B in FEN = onderaan (squares 21-32) = white pieces in ons spel
        if square_num in first_player_pieces:
            return SimpleNamespace(color='black', is_king=False, symbol=lambda: 'b')
        elif square_num in first_player_kings:
            return SimpleNamespace(color='black', is_king=True, symbol=lambda: 'B')
        elif square_num in second_player_pieces:
            return SimpleNamespace(color='white', is_king=False, symbol=lambda: 'w')
        elif square_num in second_player_kings:
            return SimpleNamespace(color='white', is_king=True, symbol=lambda: 'W')
        
        return None
    
    def get_legal_moves_from(self, chess_notation):
        """
        Geef alle legale zetten vanaf een positie
        
        Args:
            chess_notation: String zoals 'e3', 'a1', etc.
            
        Returns:
            List van chess notaties waar naartoe gezet kan worden (UPPERCASE zoals chess)
        """
        square_num = self.CHESS_TO_CHECKERS.get(chess_notation.upper())
        if square_num is None:
            return []
        
        legal_destinations = []
        
        for move in self.board.legal_moves():
            move_str = move.pdn_move
            
            # Parse move (format: "square1-square2" of "square1xsquare2xsquare3")
            if 'x' in move_str:
                squares = move_str.split('x')
            else:
                squares = move_str.split('-')
            
            from_square = int(squares[0])
            
            if from_square == square_num:
                to_square = int(squares[-1])
                to_chess = self.CHECKERS_TO_CHESS.get(to_square)
                if to_chess and to_chess not in legal_destinations:
                    # Return UPPERCASE zoals chess doet (voor LED mapping)
                    legal_destinations.append(to_chess)
        
        return legal_destinations
    
    def make_move(self, from_pos, to_pos):
        """
        Voer zet uit
        
        Args:
            from_pos: Van positie (bijv. 'E3')
            to_pos: Naar positie (bijv. 'F4')
            
        Returns:
            True als zet geldig was, False anders
        """
        from_square = self.CHESS_TO_CHECKERS.get(from_pos.upper())
        to_square = self.CHESS_TO_CHECKERS.get(to_pos.upper())
        
        if from_square is None or to_square is None:
            return False
        
        for move in self.board.legal_moves():
            move_str = move.pdn_move
            
            if 'x' in move_str:
                squares = move_str.split('x')
            else:
                squares = move_str.split('-')
            
            move_from = int(squares[0])
            move_to = int(squares[-1])
            
            if move_from == from_square and move_to == to_square:
                self.board.push(move)
                return True
        
        return False
    
    def is_game_over(self):
        """Check of spel afgelopen is"""
        return self.board.is_over()
    
    def get_game_result(self):
        """Geef resultaat van spel"""
        if not self.board.is_over():
            return "Game in progress"
        
        result = self.board.result()
        if result == "1-0":
            return "White wins!"
        elif result == "0-1":
            return "Black wins!"
        else:
            return "Draw"
    
    def whose_turn(self):
        """Geef wiens beurt het is"""
        # pydraughts: board.turn convention check
        return "white" if self.board.turn else "black"
    
    def get_move_number(self):
        """Geef huidige move number"""
        # pydraughts board heeft move_stack voor gespeelde zetten
        return len(self.board.move_stack) // 2 + 1
    
    def is_in_check(self):
        """Check of huidige speler schaak staat (niet van toepassing bij dammen)"""
        return False
    
    def is_checkmate(self):
        """Check of het schaakmat is (niet van toepassing bij dammen)"""
        return False
    
    def is_stalemate(self):
        """Check of het pat is (niet van toepassing bij dammen)"""
        return False
    
    def get_captured_pieces(self):
        """
        Bereken welke stukken zijn geslagen
        
        Returns:
            Dict met 'white' en 'black' keys, values zijn lists
        """
        # Voor checkers: tel hoeveel stukken ontbreken t.o.v. start positie
        # Start: 12 stukken per kleur
        position = self.board.fen
        parts = position.split(':')
        
        white_count = 0
        black_count = 0
        
        for part in parts:
            if part.startswith('W'):
                pieces_str = part[1:]
                if pieces_str:
                    white_count = len(pieces_str.split(','))
            elif part.startswith('B'):
                pieces_str = part[1:]
                if pieces_str:
                    black_count = len(pieces_str.split(','))
        
        # Geslagen stukken = 12 - huidige aantal
        white_captured = 12 - black_count  # Wit heeft zwart geslagen
        black_captured = 12 - white_count  # Zwart heeft wit geslagen
        
        # Return piece types ('man' voor normale stukken, 'king' kunnen we niet onderscheiden)
        # In checkers tellen we gewoon aantal geslagen stukken als 'man'
        return {
            'white': ['man'] * white_captured,  # Zwarte stukken geslagen door wit
            'black': ['man'] * black_captured   # Witte stukken geslagen door zwart
        }
    
    def get_last_move(self):
        """
        Geef laatste zet in leesbare notatie
        
        Returns:
            String zoals '12-16' of None als geen zetten gedaan
        """
        if not self.board.move_stack:
            return None
        
        last_move = self.board.move_stack[-1]
        return last_move.pdn_move
    
    def get_fen(self):
        """Geef FEN string van huidige positie"""
        return self.board.fen
