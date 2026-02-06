#!/usr/bin/env python3
"""
Chess Engine Integration

Deze module beheert de schaaklogica via de python-chess library.
Het is het kloppend hart van het spel en valideert alle zetten.

Functionaliteit:
- Board state management (positie van alle stukken)
- Legal move validation (controleert of zetten toegestaan zijn)
- Game state detection (schaak, schaakmat, remise)
- Move generation voor elke positie
- Undo/redo functionaliteit

Hoofdklasse:
- ChessEngine: Wrapper rond python-chess.Board met helper methods

Wordt gebruikt door: chessgame.py (main loop), ChessGUI (visualisatie)
"""

import chess


class ChessEngine:
    """Wrapper voor python-chess engine"""
    
    def __init__(self):
        """Initialiseer nieuw schaakbord in startpositie"""
        self.board = chess.Board()
        self.selected_square = None
        self.last_sensor_state = {}
    
    def get_board(self):
        """Geef het chess.Board object"""
        return self.board
    
    def reset(self):
        """Reset bord naar startpositie"""
        self.board.reset()
        self.selected_square = None
    
    def get_piece_at(self, chess_notation):
        """
        Geef stuk op positie
        
        Args:
            chess_notation: String zoals 'e4', 'a1', etc.
            
        Returns:
            chess.Piece of None
        """
        try:
            square = chess.parse_square(chess_notation.lower())
            return self.board.piece_at(square)
        except:
            return None
    
    def get_legal_moves_from(self, chess_notation):
        """
        Geef alle legale zetten vanaf een positie
        
        Args:
            chess_notation: String zoals 'e2', 'a1', etc.
            
        Returns:
            List van chess notaties waar naartoe gezet kan worden
        """
        try:
            from_square = chess.parse_square(chess_notation.lower())
            
            # Vind alle legal moves vanaf dit veld
            legal_destinations = []
            for move in self.board.legal_moves:
                if move.from_square == from_square:
                    dest = chess.square_name(move.to_square).upper()
                    legal_destinations.append(dest)
            
            return legal_destinations
        except:
            return []
    
    def make_move(self, from_pos, to_pos):
        """
        Voer zet uit
        
        Args:
            from_pos: Van positie (bijv. 'E2')
            to_pos: Naar positie (bijv. 'E4')
            
        Returns:
            True als zet geldig was, False anders
        """
        try:
            from_square = chess.parse_square(from_pos.lower())
            to_square = chess.parse_square(to_pos.lower())
            move = chess.Move(from_square, to_square)
            
            if move in self.board.legal_moves:
                self.board.push(move)
                return True
            return False
        except:
            return False
    
    def undo_move(self):
        """Maak laatste zet ongedaan"""
        try:
            self.board.pop()
            return True
        except:
            return False
    
    def is_game_over(self):
        """Check of spel afgelopen is"""
        return self.board.is_game_over()
    
    def get_game_result(self):
        """Geef resultaat van spel"""
        if self.board.is_checkmate():
            return "Checkmate!"
        elif self.board.is_stalemate():
            return "Stalemate"
        elif self.board.is_insufficient_material():
            return "Draw - Insufficient material"
        elif self.board.is_fifty_moves():
            return "Draw - 50 move rule"
        elif self.board.is_repetition():
            return "Draw - Repetition"
        return "Game in progress"
    
    def get_captured_pieces(self):
        """
        Bereken welke stukken zijn geslagen
        
        Returns:
            Dict met 'white' en 'black' keys, values zijn lists van piece symbols
        """
        # Start positie heeft deze stukken:
        start_pieces = {
            'p': 8, 'n': 2, 'b': 2, 'r': 2, 'q': 1, 'k': 1,  # black
            'P': 8, 'N': 2, 'B': 2, 'R': 2, 'Q': 1, 'K': 1   # white
        }
        
        # Tel huidige stukken
        current_pieces = {}
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                symbol = piece.symbol()
                current_pieces[symbol] = current_pieces.get(symbol, 0) + 1
        
        # Bereken wat er geslagen is
        captured = {'white': [], 'black': []}
        
        for piece_type, count in start_pieces.items():
            current_count = current_pieces.get(piece_type, 0)
            captured_count = count - current_count
            
            if captured_count > 0:
                if piece_type.isupper():  # White piece captured
                    captured['white'].extend([piece_type] * captured_count)
                else:  # Black piece captured
                    captured['black'].extend([piece_type] * captured_count)
        
        return captured
    
    def get_move_number(self):
        """Geef huidige move number"""
        return self.board.fullmove_number
    
    def is_in_check(self):
        """Check of huidige speler schaak staat"""
        return self.board.is_check()
    
    def is_checkmate(self):
        """Check of het schaakmat is"""
        return self.board.is_checkmate()
    
    def is_stalemate(self):
        """Check of het pat (stalemate) is"""
        return self.board.is_stalemate()
    
    def is_game_over(self):
        """Check of het spel afgelopen is"""
        return self.board.is_game_over()
    
    def get_last_move(self):
        """
        Geef laatste zet in leesbare notatie
        
        Returns:
            String zoals 'e2e4' of None als geen zetten gedaan
        """
        try:
            last_move = self.board.peek()
            return self.board.san(last_move)
        except:
            return None
