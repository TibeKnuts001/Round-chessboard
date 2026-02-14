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
from lib.core.base_engine import BaseEngine


class ChessEngine(BaseEngine):
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
    
    def make_move(self, from_pos, to_pos, promotion=None):
        """
        Voer zet uit
        
        Args:
            from_pos: Van positie (bijv. 'E2')
            to_pos: Naar positie (bijv. 'E4')
            promotion: Promotion piece ('q', 'r', 'b', 'n') of None
            
        Returns:
            Dict met 'success', 'needs_promotion', 'promotion_piece' of False
        """
        try:
            from_square = chess.parse_square(from_pos.lower())
            to_square = chess.parse_square(to_pos.lower())
            
            # Check if this is a pawn promotion move
            piece = self.board.piece_at(from_square)
            if piece and piece.piece_type == chess.PAWN:
                # Check if pawn reaches last rank
                to_rank = chess.square_rank(to_square)
                if (piece.color == chess.WHITE and to_rank == 7) or (piece.color == chess.BLACK and to_rank == 0):
                    # This is a promotion!
                    if promotion is None:
                        # Need to ask for promotion choice
                        return {'success': False, 'needs_promotion': True}
                    else:
                        # Create promotion move
                        promotion_piece = {
                            'q': chess.QUEEN,
                            'r': chess.ROOK,
                            'b': chess.BISHOP,
                            'n': chess.KNIGHT
                        }.get(promotion.lower(), chess.QUEEN)
                        
                        move = chess.Move(from_square, to_square, promotion=promotion_piece)
                        if move in self.board.legal_moves:
                            self.board.push(move)
                            return {'success': True, 'promotion_piece': promotion}
                        return False
            
            # Normal move (no promotion)
            move = chess.Move(from_square, to_square)
            if move in self.board.legal_moves:
                # Check if this is a castling move (king moving 2 squares)
                is_castling = piece and piece.piece_type == chess.KING and abs(chess.square_file(from_square) - chess.square_file(to_square)) == 2
                
                rook_intermediate = []
                if is_castling:
                    # Determine rook positions for castling
                    if chess.square_file(to_square) == 6:  # Kingside (O-O)
                        rook_from_file = 7
                        rook_to_file = 5
                    else:  # Queenside (O-O-O)
                        rook_from_file = 0
                        rook_to_file = 3
                    
                    rank = chess.square_rank(from_square)
                    rook_from = chess.square_name(chess.square(rook_from_file, rank)).upper()
                    rook_to = chess.square_name(chess.square(rook_to_file, rank)).upper()
                    rook_intermediate = [rook_from, rook_to]
                
                self.board.push(move)
                
                # Return dict with rook movement for castling
                if is_castling:
                    return {'success': True, 'intermediate': rook_intermediate}
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
    
    def get_last_move_squares(self):
        """
        Geef from/to squares van laatste zet (inclusief rook bij castling)
        
        Returns:
            Tuple (from_square, to_square, intermediate) in chess notatie
            intermediate bevat [rook_from, rook_to] bij castling, anders []
        """
        try:
            if len(self.board.move_stack) > 0:
                last_move = self.board.peek()
                from_square = chess.square_name(last_move.from_square)
                to_square = chess.square_name(last_move.to_square)
                
                # Check if this was a castling move
                intermediate = []
                piece = self.board.piece_at(last_move.to_square)
                if piece and piece.piece_type == chess.KING:
                    # Check if king moved 2 squares (castling)
                    if abs(chess.square_file(last_move.from_square) - chess.square_file(last_move.to_square)) == 2:
                        # This was castling, calculate rook positions
                        if chess.square_file(last_move.to_square) == 6:  # Kingside
                            rook_from_file = 7
                            rook_to_file = 5
                        else:  # Queenside
                            rook_from_file = 0
                            rook_to_file = 3
                        
                        rank = chess.square_rank(last_move.to_square)
                        rook_from = chess.square_name(chess.square(rook_from_file, rank)).upper()
                        rook_to = chess.square_name(chess.square(rook_to_file, rank)).upper()
                        intermediate = [rook_from, rook_to]
                
                return (from_square.upper(), to_square.upper(), intermediate)
            return (None, None, [])
        except:
            return (None, None, [])
