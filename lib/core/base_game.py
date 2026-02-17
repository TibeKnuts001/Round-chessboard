#!/usr/bin/env python3
"""
Base Game Class

Abstracte base class met alle herbruikbare game loop logic.
Bevat alle functionaliteit die gedeeld wordt tussen chess, checkers, etc.

Shared functionaliteit:
- Hardware interface (LEDs, sensors)
- Sensor reading en change detection
- Board validation (fysiek vs engine state)
- LED feedback (selection, legal moves, warnings)
- Temp message systeem
- Pause handling bij board mismatches
- Brightness management

Game-specifieke functionaliteit (moet geïmplementeerd worden door subclass):
- Game engine (chess.Board vs checkers board)
- GUI rendering (piece symbols, board layout)
- AI opponent (Stockfish vs checkers AI)
- Piece movement rules (via engine)

Subclasses moeten implementeren:
- _create_engine(): Return game-specifieke engine instance
- _create_gui(): Return game-specifieke GUI instance
- _create_ai(): Return AI instance (optioneel, mag None zijn)
"""

import pygame
import time
from abc import ABC, abstractmethod
from lib.hardware.leds import LEDController
from lib.hardware.sensors import SensorReader
from lib.hardware.mapping import ChessMapper  # TODO: Hernoemen naar BoardMapper
from lib.settings import Settings
from lib.effects.led_animations import LEDAnimator
from lib.gui.screensaver import Screensaver
from lib.audio.sound_manager import SoundManager


class BaseGame(ABC):
    """Abstract base class voor board games met sensor integratie"""
    
    def __init__(self, brightness=128):
        """
        Initialiseer base game
        
        Args:
            brightness: LED brightness value (0-255)
        """
        print(f"Initialiseer {self.__class__.__name__}...")
        
        # Hardware (shared tussen alle games)
        self.leds = LEDController(brightness=brightness)
        self.sensors = SensorReader()
        
        # Game engine (game-specifiek, wordt gemaakt door subclass)
        self.engine = self._create_engine()
        
        # GUI (game-specifiek, wordt gemaakt door subclass)
        self.gui = self._create_gui(self.engine)
        self.gui._game_instance = self  # Geef GUI referentie naar game voor state access
        self.screen = self.gui.screen  # Voor snelle toegang
        
        # AI opponent (game-specifiek, optioneel)
        self.ai = None
        if self._is_vs_computer_enabled():
            self.ai = self._create_ai()
        
        # Shared state tracking
        self.previous_sensor_state = {}
        self.selected_square = None
        self.game_started = False  # Spel moet gestart worden met New Game button
        self.invalid_return_position = None  # Touch-move violation tracking
        self.board_mismatch_positions = []  # Board validation errors
        self.previous_mismatch_positions = []  # Track voor clearing LEDs
        self.game_paused = False  # Pause bij board mismatch
        self.previous_brightness = brightness
        self.temp_message = None  # Tijdelijke berichten
        self.temp_message_timer = 0  # Wanneer bericht verdwijnt
        self.last_blink_state = None  # Track LED blink state om onnodige updates te voorkomen
        self.last_mismatch_blink_state = False  # Track mismatch blink state voor sound effect
        self.screen_dirty = True  # Flag: herteken nodig (CPU optimalisatie)
        self.last_gui_result = {}  # Cache laatste gui_result voor button detection
        self.ai_move_pending = None  # Track AI move execution: {'from': pos, 'to': pos, 'intermediate': [], 'piece_removed': False}
        self.castling_pending = None  # Track castling rook movement: {'rook_from': pos, 'rook_to': pos, 'rook_removed': False}
        
        # Tutorial mode variables
        self.tutorial_active = False
        self.tutorial_time = 0
        self.tutorial_step = 0
        self.tutorial_step_duration = 1.5  # seconds per step
        
        # LED Animator voor idle effects
        self.led_animator = LEDAnimator(self.leds)
        self.led_animator.start_random_animation()  # Start animatie bij startup
        
        # Screensaver (start na 1 minuut inactiviteit als game niet gestart)
        self.screensaver = Screensaver(self.screen, "assets/screensaver/screensaver.png", self.gui.settings)
        self.screensaver_active = False
        self.screensaver_starting = False  # Flag voor delayed start
        self.screensaver_start_time = 0
        self.last_activity_time = time.time()
        self.screensaver_timeout = 60.0  # 1 minuut
        
        # Sound Manager voor game sound effects
        self.sound_manager = SoundManager(self.gui.settings)
        
        print(f"{self.__class__.__name__} klaar!")
    
    @abstractmethod
    def _create_engine(self):
        """
        Maak game-specifieke engine
        
        Returns:
            BaseEngine subclass instance (ChessEngine, CheckersEngine, etc.)
        """
        pass
    
    def _update_rotated_color(self):
        """
        Update welke kleur gespiegeld moet worden (rechts na rotatie).
        Roept game-specifieke detectie aan op board renderer.
        """
        if hasattr(self.gui.board_renderer, 'detect_rotated_color'):
            # Voor chess
            if hasattr(self.engine, 'get_board'):
                self.gui.board_renderer.detect_rotated_color(self.engine.get_board())
            # Voor checkers
            elif hasattr(self.gui, '_get_current_board_state'):
                board_state = self.gui._get_current_board_state()
                self.gui.board_renderer.detect_rotated_color(board_state)
            
            # Force piece cache refresh zodat rotatie zichtbaar wordt
            self.gui.cached_pieces = None
            if hasattr(self.gui, 'last_board_state'):
                self.gui.last_board_state = None
            if hasattr(self.gui, 'last_board_fen'):
                self.gui.last_board_fen = None
            self.screen_dirty = True
    
    @abstractmethod
    def _create_gui(self, engine):
        """
        Maak game-specifieke GUI
        
        Args:
            engine: Game engine instance
            
        Returns:
            BaseGUI subclass instance (ChessGUI, CheckersGUI, etc.)
        """
        pass
    
    @abstractmethod
    def _create_ai(self):
        """
        Maak game-specifieke AI opponent (optioneel)
        
        Returns:
            AI instance of None als niet beschikbaar
        """
        pass
    
    @abstractmethod
    def make_computer_move(self):
        """
        Laat computer een zet doen (game-specifiek)
        
        Moet geïmplementeerd worden door subclass omdat:
        - Chess: Stockfish UCI interface
        - Checkers: Eigen AI algoritme
        """
        pass
    
    def _is_vs_computer_enabled(self):
        """
        Check of VS Computer mode aan staat (kan worden overschreven door subclass)
        
        Returns:
            bool: True als VS Computer mode enabled is
        """
        # Default implementatie - subclass kan overschrijven voor game-specifieke sectie
        return self.gui.settings.get('play_vs_computer', False)
    
    def _load_test_position(self):
        """
        Load test FEN position (chess only)
        
        FEN: 8/2p5/1p1p1k2/p2Pp3/P1P1Pp2/5P2/5K2/8 w - - 0 1
        """
        # Check if this is a chess game with a board that supports FEN
        if hasattr(self.engine, 'board') and hasattr(self.engine.board, 'set_fen'):
            try:
                test_fen = "8/2p5/1p1p1k2/p2Pp3/P1P1Pp2/5P2/5K2/8 w - - 0 1"
                self.engine.board.set_fen(test_fen)
                print(f"Loaded test position: {test_fen}")
                self.game_started = True
                self.last_activity_time = time.time()
            except Exception as e:
                print(f"Error loading test position: {e}")
    
    def read_sensors(self):
        """
        Lees sensor state en converteer naar dict met posities
        
        Returns:
            Dict met posities en sensor states (True = stuk aanwezig)
        """
        sensor_values = self.sensors.read_all()
        
        # Inverse logica: LOW = magneet aanwezig (stuk staat er)
        active_sensors = {}
        for i in range(64):
            pos = ChessMapper.sensor_to_chess(i)  # TODO: Gebruik board_notation_to_sensor mapping
            if pos:
                # True = stuk staat op veld (sensor LOW)
                active_sensors[pos] = not sensor_values[i]
        
        return active_sensors
    
    def validate_board_state(self, sensor_state):
        """
        Vergelijk fysieke board state met engine state
        
        Returns:
            List van posities waar mismatch is (stuk zou er moeten zijn maar niet gedetecteerd,
            of stuk staat er maar hoort er niet te zijn)
        """
        mismatches = []
        
        for row in range(8):
            for col in range(8):
                pos = f"{chr(65 + col)}{8 - row}"
                engine_has_piece = self.engine.get_piece_at(pos) is not None
                sensor_has_piece = sensor_state.get(pos, False)
                
                # Mismatch: engine heeft stuk, sensor detecteert niets
                if engine_has_piece and not sensor_has_piece:
                    mismatches.append(pos)
                # Mismatch: sensor detecteert stuk, maar engine heeft er geen
                elif sensor_has_piece and not engine_has_piece:
                    mismatches.append(pos)
        
        return mismatches
    
    def count_pieces(self):
        """
        Tel totaal aantal stukken op het bord
        
        Returns:
            int: Totaal aantal stukken
        """
        count = 0
        for row in range(8):
            for col in range(8):
                pos = f"{chr(65 + col)}{8 - row}"
                if self.engine.get_piece_at(pos) is not None:
                    count += 1
        return count
    
    def detect_changes(self, current_state, previous_state):
        """
        Detecteer veranderingen in sensor state
        
        Returns:
            (added, removed) - sets van posities
        """
        current_positions = set(pos for pos, active in current_state.items() if active)
        previous_positions = set(pos for pos, active in previous_state.items() if active)
        
        added = current_positions - previous_positions
        removed = previous_positions - current_positions
        
        return added, removed
    
    def handle_sensor_changes(self, added, removed):
        """
        Handle sensor veranderingen
        
        Args:
            added: Set van posities waar stukken zijn neergezet
            removed: Set van posities waar stukken zijn weggehaald
        """
        # Reset activity timer
        if added or removed:
            self.last_activity_time = time.time()
        
        for pos in removed:
            print(f"[SENSOR EVENT] Stuk weggehaald van {pos}")
            self.handle_piece_removed(pos)
        for pos in added:
            print(f"[SENSOR EVENT] Stuk neergezet op {pos}")
            self.handle_piece_added(pos)
    
    def update_leds(self, positions, color=(255, 255, 255, 0), capture_positions=None, capture_color=(255, 0, 0, 0)):
        """
        Light LEDs op specifieke posities
        
        Args:
            positions: List van positie notaties (normale moves)
            color: (r, g, b, w) tuple voor normale moves
            capture_positions: List van positie notaties voor captures (optioneel)
            capture_color: (r, g, b, w) tuple voor captures
        """
        if capture_positions is None:
            capture_positions = []
        
        # Clear all LEDs
        self.leds.clear()
        
        # Light up normal move positions
        for pos in positions:
            sensor_num = ChessMapper.chess_to_sensor(pos)  # TODO: Gebruik board mapping
            if sensor_num is not None:
                r, g, b, w = color
                self.leds.set_led(sensor_num, r, g, b, w)
        
        # Light up capture positions (rood)
        for pos in capture_positions:
            sensor_num = ChessMapper.chess_to_sensor(pos)
            if sensor_num is not None:
                r, g, b, w = capture_color
                self.leds.set_led(sensor_num, r, g, b, w)
        
        self.leds.show()
    
    def handle_piece_removed(self, position):
        """
        Handle wanneer stuk weggehaald wordt
        
        Args:
            position: Positie notatie van waar stuk weggehaald is
        """
        print(f"\nStuk weggehaald van {position}")
        
        # Debug castling pending state
        if self.castling_pending:
            print(f"  DEBUG: castling_pending.rook_from = '{self.castling_pending.get('rook_from')}'")
            print(f"  DEBUG: position = '{position}'")
            print(f"  DEBUG: Match check = {self.castling_pending.get('rook_from', '').lower() == position.lower()}")
        
        # Check of dit castling rook removal is (case-insensitive)
        if self.castling_pending and self.castling_pending.get('rook_from', '').lower() == position.lower():
            print(f"  Castling rook opgepakt - markeer als rook_removed")
            self.castling_pending['rook_removed'] = True
            return  # Skip normale handling
        
        # Als er een castling pending is maar dit is NIET de rook, blokkeer dan andere moves
        if self.castling_pending:
            print(f"  Castling pending - speler mag geen andere zet doen! Verplaats eerst de rook.")
            self.sound_manager.play_mismatch()
            self.show_temp_message("Please move the rook to complete castling!", duration=2000)
            return  # Blokkeer andere moves
        
        # Debug AI move pending state
        if self.ai_move_pending:
            print(f"  DEBUG: ai_move_pending.from = '{self.ai_move_pending.get('from')}'")
            print(f"  DEBUG: position = '{position}'")
            print(f"  DEBUG: Match check = {self.ai_move_pending.get('from', '').lower() == position.lower()}")
        
        # Check of dit AI move execution is (case-insensitive)
        if self.ai_move_pending and self.ai_move_pending.get('from', '').lower() == position.lower():
            print(f"  AI move stuk opgepakt - markeer als piece_removed")
            self.ai_move_pending['piece_removed'] = True
            return  # Skip normale handling
        
        # Als er een AI move pending is maar dit is NIET de AI move, blokkeer dan speler moves
        if self.ai_move_pending:
            print(f"  AI move pending - speler mag geen zet doen! Wacht tot AI move is uitgevoerd.")
            self.sound_manager.play_mismatch()
            self.show_temp_message("Please execute AI move first!", duration=2000)
            return  # Blokkeer speler moves
        
        # Check of we terugkomen van een invalid return (rood knipperen -> blauw knipperen)
        if self.invalid_return_position == position:
            print(f"  Terug opgepakt van ongeldige return positie - terug naar normaal blauw")
            self.invalid_return_position = None
        
        # Check of er een stuk staat volgens engine
        piece = self.engine.get_piece_at(position)
        if piece:
            print(f"  Stuk: {piece.symbol() if hasattr(piece, 'symbol') else piece}")
            
            # Haal legal moves op
            legal_moves = self.engine.get_legal_moves_from(position)
            
            # Parse legal_moves (kan list of dict zijn voor checkers)
            if isinstance(legal_moves, dict):
                destinations = legal_moves.get('destinations', [])
                intermediate = legal_moves.get('intermediate', [])
                all_moves = destinations + intermediate
                has_moves = bool(destinations)  # Alleen destinations tellen
            else:
                all_moves = legal_moves
                has_moves = bool(legal_moves)
            
            if has_moves:
                print(f"  Legal moves: {', '.join(all_moves)}")
                
                # Toon opgepakt stuk in GUI
                self.gui.set_selected_piece(piece, position)
                
                # Highlight legal move posities (geef originele legal_moves door)
                self.gui.highlight_squares(legal_moves)
                
                # Light up LEDs voor legal moves
                # Haal capture_squares op van GUI (na highlight_squares call)
                capture_squares = getattr(self.gui, 'capture_squares', [])
                normal_squares = getattr(self.gui, 'highlighted_squares', all_moves)
                
                # Groen voor normale moves, rood voor captures
                self.update_leds(
                    normal_squares, 
                    color=(0, 255, 0, 0),  # Groen
                    capture_positions=capture_squares,
                    capture_color=(255, 0, 0, 0)  # Rood
                )
                
                # Onthoud geselecteerd veld
                self.selected_square = position
            else:
                # Geen legal moves - waarschijnlijk een vijandelijk stuk dat je wilt capturen
                # Negeer stil (geen error message) - wacht tot speler eigen stuk oppakt
                print("  Geen legal moves - negeer (waarschijnlijk vijandelijk stuk)")
        else:
            print("  Geen stuk op deze positie volgens engine")
    
    def handle_piece_added(self, position):
        """
        Handle wanneer stuk toegevoegd wordt
        
        Args:
            position: Positie notatie waar stuk neergezet is
        """
        print(f"\nStuk neergezet op {position}")
        
        # Check of dit castling rook placement completion is (case-insensitive)
        if (self.castling_pending and 
            self.castling_pending.get('rook_removed')):
            
            rook_to_pos = self.castling_pending.get('rook_to', '').lower()
            pos_lower = position.lower()
            
            # Check of dit de rook destination is
            if rook_to_pos == pos_lower:
                print(f"  Castling volledig uitgevoerd! Rook verplaatst naar {position}")
                
                # Toon witte LEDs voor voltooide castling (king + rook positions)
                self.leds.clear()
                rook_from = self.castling_pending.get('rook_from')
                rook_to = self.castling_pending.get('rook_to')
                
                from_sensor = ChessMapper.chess_to_sensor(rook_from) if rook_from else None
                to_sensor = ChessMapper.chess_to_sensor(rook_to) if rook_to else None
                
                if from_sensor is not None:
                    self.leds.set_led(from_sensor, 100, 100, 100, 20)  # WIT
                if to_sensor is not None:
                    self.leds.set_led(to_sensor, 100, 100, 100, 20)  # WIT
                
                self.leds.show()
                
                # Clear castling_pending
                self.castling_pending = None
                if hasattr(self, '_castling_leds_set'):
                    self._castling_leds_set = False
                print("  castling_pending cleared - speler kan weer bewegen")
                return  # Skip normale handling
            else:
                # Rook neergezet op verkeerde positie
                print(f"  WAARSCHUWING: Rook neergezet op {position}, maar castling verwacht {rook_to_pos}")
                self.sound_manager.play_mismatch()
                self.show_temp_message(f"Rook must go to {self.castling_pending.get('rook_to')}!", duration=2000)
                # Laat rook daar - speler moet het naar de juiste plek verplaatsen
                return  # Skip normale handling
        
        # Debug AI move pending state
        if self.ai_move_pending:
            print(f"  DEBUG: ai_move_pending = {self.ai_move_pending}")
            print(f"  DEBUG: position = '{position}' (type: {type(position)})")
            print(f"  DEBUG: to = '{self.ai_move_pending.get('to')}' (type: {type(self.ai_move_pending.get('to'))})")
            print(f"  DEBUG: position.lower() = '{position.lower()}'")
            print(f"  DEBUG: to.lower() = '{self.ai_move_pending.get('to', '').lower()}'")
            print(f"  DEBUG: piece_removed = {self.ai_move_pending.get('piece_removed')}")
            print(f"  DEBUG: Match check = {self.ai_move_pending.get('to', '').lower() == position.lower()}")
        
        # Check of dit AI move execution completion is (case-insensitive)
        # Voor multi-captures moet het stuk op de final 'to' position komen, niet intermediate
        if (self.ai_move_pending and 
            self.ai_move_pending.get('piece_removed')):
            
            to_pos = self.ai_move_pending.get('to', '').lower()
            pos_lower = position.lower()
            
            # Check of dit de final destination is
            if to_pos == pos_lower:
                print(f"  AI move volledig uitgevoerd! Toon witte LEDs.")
                
                # Toon witte LEDs voor uitgevoerde move
                self.leds.clear()
                from_pos = self.ai_move_pending.get('from')
                to_pos_orig = self.ai_move_pending.get('to')
                intermediate = self.ai_move_pending.get('intermediate', [])
                
                from_sensor = ChessMapper.chess_to_sensor(from_pos) if from_pos else None
                to_sensor = ChessMapper.chess_to_sensor(to_pos_orig) if to_pos_orig else None
                
                if from_sensor is not None:
                    self.leds.set_led(from_sensor, 100, 100, 100, 20)  # WIT
                if to_sensor is not None:
                    self.leds.set_led(to_sensor, 100, 100, 100, 20)  # WIT
                
                # Toon intermediate positions in paars
                for inter_pos in intermediate:
                    inter_sensor = ChessMapper.chess_to_sensor(inter_pos)
                    if inter_sensor is not None:
                        self.leds.set_led(inter_sensor, 80, 0, 80, 0)  # Paars
                
                self.leds.show()
                
                # Clear ai_move_pending
                self.ai_move_pending = None
                print("  ai_move_pending cleared - speler kan weer bewegen")
                return  # Skip normale handling
            else:
                # Stuk neergezet op verkeerde positie
                print(f"  WAARSCHUWING: Stuk neergezet op {position}, maar AI move verwacht {to_pos}")
                # Laat stuk daar - speler moet het naar de juiste plek verplaatsen
                return  # Skip normale handling
        
        if self.selected_square:
            # Check of stuk teruggeplaatst wordt op originele positie
            if position == self.selected_square:
                # Check strict touch-move setting
                strict_touch_move = self._is_strict_touch_move_enabled()
                
                if strict_touch_move:
                    print(f"  Strict touch-move: stuk teruggeplaatst - ROOD knipperen!")
                    
                    # Track invalid return position
                    self.invalid_return_position = position
                    
                    # Show warning message
                    self.show_temp_message("Cannot return piece - Touch-move rule!", duration=2000)
                    
                    # Play mismatch sound for touch-move violation
                    self.sound_manager.play_mismatch()
                    return
                else:
                    print(f"  Stuk teruggeplaatst op originele positie - deselecteer")
                    
                    # Clear highlights en LEDs
                    self.gui.highlight_squares([])
                    self.gui.set_selected_piece(None, None)
                    self.leds.clear()
                    self.leds.show()
                    
                    # Reset selectie
                    self.selected_square = None
                    return
            
            # Count pieces before move to detect captures
            pieces_before = self.count_pieces()
            
            # Probeer zet te maken
            move_result = self.engine.make_move(self.selected_square, position, promotion=getattr(self.gui, 'promotion_choice', None))
            
            # Reset promotion choice voor volgende moves
            if hasattr(self.gui, 'promotion_choice'):
                self.gui.promotion_choice = None
            
            # Parse result (kan bool of dict zijn)
            if isinstance(move_result, dict):
                move_success = move_result.get('success', False)
                needs_promotion = move_result.get('needs_promotion', False)
                move_intermediate = move_result.get('intermediate', [])
                
                # Check if promotion is needed
                if needs_promotion:
                    print(f"  Pawn promotion required for {self.selected_square} -> {position}")
                    # Show promotion dialog
                    self.gui.show_promotion_dialog = True
                    self.gui.promotion_from = self.selected_square
                    self.gui.promotion_to = position
                    self.gui.promotion_choice = None
                    self.screen_dirty = True
                    return
                
                # Check if this is a castling move (intermediate contains rook positions)
                if move_success and move_intermediate and len(move_intermediate) == 2:
                    # This is castling - set castling_pending to track rook movement
                    rook_from, rook_to = move_intermediate
                    self.castling_pending = {
                        'rook_from': rook_from,
                        'rook_to': rook_to,
                        'rook_removed': False
                    }
                    print(f"  Castling detected! Rook must move: {rook_from} -> {rook_to}")
                    print(f"  castling_pending = {self.castling_pending}")
            else:
                move_success = bool(move_result)
                move_intermediate = []
            
            if move_success:
                print(f"  Zet: {self.selected_square} -> {position}")
                
                # Mark game als gestart na eerste zet
                self.game_started = True
                self.last_activity_time = time.time()
                
                # Bewaar last move voor highlighting (inclusief intermediate squares)
                last_move_from = self.selected_square
                last_move_to = position
                if hasattr(self.gui, 'set_last_move'):
                    self.gui.set_last_move(last_move_from, last_move_to, move_intermediate)
                
                # Clear highlights en LEDs
                self.gui.highlight_squares([])
                self.gui.set_selected_piece(None, None)
                self.leds.clear()
                self.leds.show()
                
                # Reset selectie
                self.selected_square = None
                
                # Check if a piece was captured (piece count decreased)
                pieces_after = self.count_pieces()
                if pieces_after < pieces_before:
                    self.sound_manager.play_capture()
                
                # Check game status
                if self.engine.is_game_over():
                    print(f"\n*** {self.engine.get_game_result()} ***\n")
                    # Play checkmate sound
                    if hasattr(self.engine, 'is_checkmate') and self.engine.is_checkmate():
                        self.sound_manager.play_checkmate()
                else:
                    # Check for check
                    if hasattr(self.engine, 'is_in_check') and self.engine.is_in_check():
                        self.sound_manager.play_check()
                    
                    # Als VS Computer aan staat, laat computer zet doen
                    if self._is_vs_computer_enabled() and self.ai:
                        # Eerst GUI hertekenen met player move
                        self.screen.fill(self.gui.COLOR_BG)
                        self.gui.draw_board()
                        self.gui.draw_pieces()
                        self.gui.draw_debug_overlays()
                        if self.gui.settings.get('show_coordinates', True):
                            self.gui.draw_coordinates()
                        self.gui.draw_sidebar()
                        pygame.display.flip()
                        
                        # Nu computer zet doen
                        self.make_computer_move()
            else:
                print(f"  Ongeldige zet: {self.selected_square} -> {position}")
                # Play mismatch sound for invalid move
                self.sound_manager.play_mismatch()
    
    def show_temp_message(self, message, duration=2000):
        """Toon tijdelijk bericht op scherm"""
        self.temp_message = message
        self.temp_message_timer = pygame.time.get_ticks() + duration
    
    def run(self):
        """
        Main game loop (shared tussen alle games)
        
        Deze methode bevat ALLE gemeenschappelijke game loop logic.
        Game-specifieke rendering wordt gedelegeerd naar GUI classes.
        """
        print("\n" + "=" * 50)
        print(f"{self.__class__.__name__} Started")
        print("=" * 50)
        print("Druk op ESC of sluit venster om te stoppen\n")
        
        clock = pygame.time.Clock()
        running = True
        
        # Initiële sensor state
        current_sensors = self.read_sensors()
        self.previous_sensor_state = current_sensors.copy()
        
        try:
            while running:
                # Handle delayed screensaver start
                current_time = time.time()
                if self.screensaver_starting:
                    elapsed = current_time - self.screensaver_start_time
                    if elapsed > 0.5:
                        # 500ms verstreken, nu echt starten
                        self.screensaver_active = True
                        self.screensaver_starting = False
                        self.screensaver.start_audio()
                        self.leds.clear()
                        self.leds.show()
                        print(f"Screensaver gestart (delayed na {elapsed:.2f}s)")
                    else:
                        # Nog aan het wachten
                        if int(elapsed * 10) % 2 == 0:  # Print elke 0.2s
                            print(f"Waiting for screensaver... {elapsed:.2f}s / 0.5s")
                
                # Check screensaver status (ALLEEN als game NIET gestart EN NIET in assisted setup EN NIET in tutorial)
                if not self.game_started and not self.gui.assisted_setup_mode and not self.tutorial_active:
                    if not self.screensaver_active and not self.screensaver_starting and (current_time - self.last_activity_time) > self.screensaver_timeout:
                        # Start screensaver
                        self.screensaver_active = True
                        self.screensaver.start_audio()
                        self.leds.clear()
                        self.leds.show()
                        print("Screensaver gestart (timeout)")
                
                # Als game gestart is of assisted setup actief of tutorial actief: zorg dat screensaver UIT is
                if self.game_started or self.gui.assisted_setup_mode or self.tutorial_active:
                    if self.screensaver_active or self.screensaver_starting:
                        self.screensaver.stop_audio()
                        self.screensaver_active = False
                        self.screensaver_starting = False
                        # Force een volledige redraw van de game UI
                        self.screen_dirty = True
                        self.gui.draw(self.temp_message, self.temp_message_timer, game_started=self.game_started)
                        pygame.display.flip()
                        print("Screensaver gestopt (game actief)")
                
                # Screensaver mode - simplified rendering
                if self.screensaver_active:
                    # Update screensaver animatie
                    dt = clock.get_time() / 1000.0  # Convert ms to seconds
                    self.screensaver.update(dt)
                    self.screensaver.draw()
                    pygame.display.flip()
                    
                    # Check voor events die screensaver stoppen
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False
                        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                            running = False
                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            # Touch stops screensaver
                            self.screensaver.stop_audio()
                            self.screensaver_active = False
                            self.last_activity_time = current_time
                            # Force een volledige redraw van de game UI
                            self.screen_dirty = True
                            self.gui.draw(self.temp_message, self.temp_message_timer, game_started=self.game_started)
                            pygame.display.flip()
                            print("Screensaver gestopt (touch)")
                    
                    # Check sensor changes om screensaver te stoppen
                    current_sensors = self.read_sensors()
                    added, removed = self.detect_changes(current_sensors, self.previous_sensor_state)
                    if added or removed:
                        self.screensaver.stop_audio()
                        self.screensaver_active = False
                        self.last_activity_time = current_time
                        # Force een volledige redraw van de game UI
                        self.screen_dirty = True
                        self.gui.draw(self.temp_message, self.temp_message_timer, game_started=self.game_started)
                        pygame.display.flip()
                        print("Screensaver gestopt (sensor)")
                    self.previous_sensor_state = current_sensors.copy()
                    
                    clock.tick(15)  # 15 FPS voor screensaver (was 30) - CPU besparing
                    continue  # Skip normale game loop
                
                # Normale game loop
                # Update brightness indien gewijzigd
                current_brightness = self.gui.settings.get('brightness', 20)
                if current_brightness != self.previous_brightness:
                    self.leds.set_brightness(current_brightness)
                    self.previous_brightness = current_brightness
                    print(f"Brightness aangepast naar {current_brightness}%")
                
                # Update AI status indien gewijzigd (game-specifiek)
                self._update_ai_status()
                
                # Update tutorial mode if active
                if self.tutorial_active:
                    dt = clock.get_time() / 1000.0  # Convert ms to seconds
                    self._update_tutorial(dt)
                
                # Update LED blink animatie (skip if tutorial active)
                if not self.tutorial_active:
                    self._update_led_animations()
                
                # Lees sensors
                current_sensors = self.read_sensors()
                
                # Update assisted setup als actief
                if self.gui.assisted_setup_mode:
                    self._update_assisted_setup_sensors()
                
                # Update sensor debug visualisatie
                if self.gui.settings.get('debug_sensors', False, section='debug'):
                    old_states = getattr(self.gui, 'active_sensor_states', {})
                    self.gui.update_sensor_debug_states(current_sensors)
                    # Check of er veranderingen zijn in sensor states
                    if old_states != current_sensors:
                        self.screen_dirty = True
                
                # Clear temp message als timer verlopen is
                if self.temp_message and pygame.time.get_ticks() >= self.temp_message_timer:
                    self.temp_message = None
                    self.screen_dirty = True
                
                # Draw screen (only when dirty)
                if self.screen_dirty:
                    gui_result = self.gui.draw(self.temp_message, self.temp_message_timer, game_started=self.game_started)
                    
                    # Draw tutorial overlay if active
                    if self.tutorial_active:
                        self._draw_tutorial_overlay()
                    
                    pygame.display.flip()
                    self.screen_dirty = False
                    self.last_gui_result = gui_result  # Cache voor volgende frame
                else:
                    gui_result = self.last_gui_result  # Gebruik cached result
                
                # Handle events (kan screen_dirty zetten)
                running = self._handle_events(gui_result)
                
                # Detecteer sensor veranderingen (alleen als game gestart is en niet gepauzeerd)
                if self.game_started and not self.game_paused:
                    added, removed = self.detect_changes(current_sensors, self.previous_sensor_state)
                    if added or removed:
                        self.handle_sensor_changes(added, removed)
                        self.screen_dirty = True  # Herteken bij sensor changes
                        self.screen_dirty = True
                
                # Valideer board state (NA sensor handling, zodat selected_square up-to-date is)
                # Alleen valideren als: spel gestart, setting enabled, geen actieve move, EN geen AI move pending, EN geen castling pending
                if (self.game_started and 
                    not self.selected_square and 
                    not self.invalid_return_position and
                    not self.ai_move_pending and
                    not self.castling_pending and
                    self.gui.settings.get('validate_board_state', False, section='debug')):
                    old_paused_state = self.game_paused
                    self.board_mismatch_positions = self.validate_board_state(current_sensors)
                    if self.board_mismatch_positions:
                        self.game_paused = True
                        if not self.temp_message:
                            self.show_temp_message("Board mismatch! Fix sensor positions.", duration=999999)
                        # State veranderd naar invalid
                        if not old_paused_state:
                            self.screen_dirty = True
                    else:
                        if self.game_paused:
                            self.game_paused = False
                            # Clear alleen board mismatch message
                            if self.temp_message and "Board mismatch" in str(self.temp_message):
                                self.temp_message = None
                            self.screen_dirty = True  # State veranderd naar valid
                else:
                    self.board_mismatch_positions = []
                
                # Update previous state
                self.previous_sensor_state = current_sensors.copy()
                
                # Control framerate - lager voor idle (CPU besparing)
                # 10 FPS als scherm niet dirty (idle), 30 FPS bij interactie
                fps = 30 if self.screen_dirty else 10
                clock.tick(fps)
                
        except KeyboardInterrupt:
            print("\n\nGame gestopt")
        finally:
            self.cleanup()
    
    def _update_ai_status(self):
        """Update AI opponent status (game-specifiek, kan overridden worden)"""
        pass  # Default implementatie: geen AI updates
    
    def _update_led_animations(self):
        """Update LED blink animaties voor geselecteerd veld en warnings"""
        # Check eerst of er een castling rook movement pending is (heeft hoogste prioriteit)
        if self.castling_pending and not self.board_mismatch_positions:
            # Toon castling rook move: blauw voor from, groen voor to (constant, geen blink)
            if not hasattr(self, '_castling_leds_set') or not self._castling_leds_set:
                rook_from = self.castling_pending.get('rook_from')
                rook_to = self.castling_pending.get('rook_to')
                
                from_sensor = ChessMapper.chess_to_sensor(rook_from) if rook_from else None
                to_sensor = ChessMapper.chess_to_sensor(rook_to) if rook_to else None
                
                self.leds.clear()
                if from_sensor is not None:
                    self.leds.set_led(from_sensor, 0, 0, 255, 0)  # BLAUW - pak rook op
                if to_sensor is not None:
                    self.leds.set_led(to_sensor, 0, 255, 0, 0)  # GROEN - verplaats rook naar hier
                
                self.leds.show()
                self._castling_leds_set = True
                print("  Castling rook LEDs gezet (blauw/groen)")
            return
        else:
            # Clear flag als castling_pending niet meer bestaat
            if hasattr(self, '_castling_leds_set'):
                self._castling_leds_set = False
        
        # Check eerst of er een AI move pending is (heeft prioriteit, maar alleen als geen board mismatches)
        if self.ai_move_pending and not self.board_mismatch_positions:
            # Toon AI move: blauw voor from, groen voor to (constant, geen blink)
            # Alleen updaten als de state veranderd is (voorkom onnodige LED updates die flikkering veroorzaken)
            if not hasattr(self, '_ai_move_leds_set') or not self._ai_move_leds_set:
                from_pos = self.ai_move_pending.get('from')
                to_pos = self.ai_move_pending.get('to')
                intermediate = self.ai_move_pending.get('intermediate', [])
                
                from_sensor = ChessMapper.chess_to_sensor(from_pos) if from_pos else None
                to_sensor = ChessMapper.chess_to_sensor(to_pos) if to_pos else None
                
                self.leds.clear()
                if from_sensor is not None:
                    self.leds.set_led(from_sensor, 0, 0, 255, 0)  # BLAUW - pak dit stuk op
                if to_sensor is not None:
                    self.leds.set_led(to_sensor, 0, 255, 0, 0)  # GROEN - verplaats naar hier
                
                # Toon intermediate positions in geel (voor multi-captures)
                for pos in intermediate:
                    inter_sensor = ChessMapper.chess_to_sensor(pos)
                    if inter_sensor is not None:
                        self.leds.set_led(inter_sensor, 255, 255, 0, 0)  # GEEL
                
                self.leds.show()
                self._ai_move_leds_set = True
                print("  AI move LEDs gezet (blauw/groen)")
            return
        else:
            # Clear flag als ai_move_pending niet meer bestaat
            if hasattr(self, '_ai_move_leds_set'):
                self._ai_move_leds_set = False
        
        if self.selected_square:
            # Bereken knipperstaat (500ms aan, 500ms uit)
            blink_on = (pygame.time.get_ticks() // 500) % 2 == 0
            
            # Alleen updaten als blink state veranderd is (voorkom flikkering)
            if blink_on == self.last_blink_state:
                return
            
            self.last_blink_state = blink_on
            self.screen_dirty = True  # Herteken voor blinking selection indicator
            
            # Bereken legal moves 1x (voorkom herberekening die flikkering veroorzaakt)
            sensor_num = ChessMapper.chess_to_sensor(self.selected_square)
            legal_moves = self.engine.get_legal_moves_from(self.selected_square)
            
            # Parse legal_moves (kan list of dict zijn voor checkers multi-captures)
            if isinstance(legal_moves, dict):
                destinations = legal_moves.get('destinations', [])
                intermediate = legal_moves.get('intermediate', [])
            else:
                destinations = legal_moves
                intermediate = []
            
            # Check invalid return state (strict touch-move violation)
            if self.invalid_return_position:
                # ROOD knipperen voor originele positie, groen/rood voor legal moves
                if blink_on:
                    if sensor_num is not None:
                        self.leds.clear()
                        self.leds.set_led(sensor_num, 255, 0, 0, 0)  # ROOD
                        
                        # Haal capture info op van GUI voor correcte kleuren
                        capture_squares = getattr(self.gui, 'capture_squares', [])
                        normal_squares = getattr(self.gui, 'highlighted_squares', destinations)
                        
                        # Groen voor normale moves
                        for pos in normal_squares:
                            move_sensor = ChessMapper.chess_to_sensor(pos)
                            if move_sensor is not None:
                                self.leds.set_led(move_sensor, 0, 255, 0, 0)  # GROEN
                        
                        # Rood voor captures (donkerder dan violation rood)
                        for pos in capture_squares:
                            move_sensor = ChessMapper.chess_to_sensor(pos)
                            if move_sensor is not None:
                                self.leds.set_led(move_sensor, 200, 0, 0, 0)  # Donker rood voor captures
                        
                        # Geel voor intermediate (tussenposities bij multi-captures)
                        for pos in intermediate:
                            move_sensor = ChessMapper.chess_to_sensor(pos)
                            if move_sensor is not None:
                                self.leds.set_led(move_sensor, 255, 255, 0, 0)  # GEEL
                        self.leds.show()
                else:
                    # Alleen legal moves (groen/rood/geel)
                    self.leds.clear()
                    
                    # Haal capture info op van GUI voor correcte kleuren
                    capture_squares = getattr(self.gui, 'capture_squares', [])
                    normal_squares = getattr(self.gui, 'highlighted_squares', destinations)
                    
                    # Groen voor normale moves
                    for pos in normal_squares:
                        move_sensor = ChessMapper.chess_to_sensor(pos)
                        if move_sensor is not None:
                            self.leds.set_led(move_sensor, 0, 255, 0, 0)
                    
                    # Rood voor captures
                    for pos in capture_squares:
                        move_sensor = ChessMapper.chess_to_sensor(pos)
                        if move_sensor is not None:
                            self.leds.set_led(move_sensor, 255, 0, 0, 0)
                    
                    # Geel voor intermediate
                    for pos in intermediate:
                        move_sensor = ChessMapper.chess_to_sensor(pos)
                        if move_sensor is not None:
                            self.leds.set_led(move_sensor, 255, 255, 0, 0)
                    self.leds.show()
            else:
                # Normaal blauw/groen/geel knipperen
                if blink_on:
                    if sensor_num is not None:
                        self.leds.clear()
                        self.leds.set_led(sensor_num, 0, 0, 255, 0)  # BLAUW
                        
                        # Haal capture info op van GUI voor correcte kleuren
                        capture_squares = getattr(self.gui, 'capture_squares', [])
                        # highlighted_squares kan dict zijn (checkers) of list (chess)
                        hs = getattr(self.gui, 'highlighted_squares', destinations)
                        normal_squares = hs.get('destinations', []) if isinstance(hs, dict) else hs
                        
                        # Groen voor normale moves
                        for pos in normal_squares:
                            move_sensor = ChessMapper.chess_to_sensor(pos)
                            if move_sensor is not None:
                                self.leds.set_led(move_sensor, 0, 255, 0, 0)  # GROEN
                        
                        # Rood voor captures
                        for pos in capture_squares:
                            move_sensor = ChessMapper.chess_to_sensor(pos)
                            if move_sensor is not None:
                                self.leds.set_led(move_sensor, 255, 0, 0, 0)  # ROOD
                        
                        # Geel voor intermediate
                        for pos in intermediate:
                            move_sensor = ChessMapper.chess_to_sensor(pos)
                            if move_sensor is not None:
                                self.leds.set_led(move_sensor, 255, 255, 0, 0)  # GEEL
                        self.leds.show()
                else:
                    # Alleen legal moves
                    self.leds.clear()
                    
                    # Haal capture info op van GUI voor correcte kleuren
                    capture_squares = getattr(self.gui, 'capture_squares', [])
                    # highlighted_squares kan dict zijn (checkers) of list (chess)
                    hs = getattr(self.gui, 'highlighted_squares', destinations)
                    normal_squares = hs.get('destinations', []) if isinstance(hs, dict) else hs
                    
                    # Groen voor normale moves
                    for pos in normal_squares:
                        move_sensor = ChessMapper.chess_to_sensor(pos)
                        if move_sensor is not None:
                            self.leds.set_led(move_sensor, 0, 255, 0, 0)
                    
                    # Rood voor captures
                    for pos in capture_squares:
                        move_sensor = ChessMapper.chess_to_sensor(pos)
                        if move_sensor is not None:
                            self.leds.set_led(move_sensor, 255, 0, 0, 0)
                    
                    # Geel voor intermediate
                    for pos in intermediate:
                        move_sensor = ChessMapper.chess_to_sensor(pos)
                        if move_sensor is not None:
                            self.leds.set_led(move_sensor, 255, 255, 0, 0)
                    self.leds.show()
        else:
            # Geen selectie - check voor checkmate
            if self.engine.is_game_over():
                result = self.engine.get_game_result()
                if 'checkmate' in result.lower():
                    blink_on = (pygame.time.get_ticks() // 500) % 2 == 0
                    
                    if blink_on:
                        self.leds.clear()
                        
                        # Bij checkmate is board.turn de kleur van de verliezer
                        import chess
                        loser_color = self.engine.board.turn
                        winner_color = not loser_color
                        
                        # Zoek beide koningen
                        for row in range(8):
                            for col in range(8):
                                pos = f"{chr(65 + col)}{8 - row}"
                                piece = self.engine.get_piece_at(pos)
                                
                                if piece and hasattr(piece, 'piece_type'):
                                    # Chess piece (python-chess)
                                    if piece.piece_type == chess.KING:
                                        sensor_num = ChessMapper.chess_to_sensor(pos)
                                        if sensor_num is not None:
                                            # Winnaar = groen, verliezer = rood
                                            if piece.color == winner_color:
                                                self.leds.set_led(sensor_num, 0, 255, 0, 0)  # GROEN - winnaar
                                            else:
                                                self.leds.set_led(sensor_num, 255, 0, 0, 0)  # ROOD - verliezer
                        
                        # Toon ook laatste zet in wit
                        if hasattr(self.gui, 'last_move_from') and self.gui.last_move_from and self.gui.last_move_to:
                            from_sensor = ChessMapper.chess_to_sensor(self.gui.last_move_from)
                            to_sensor = ChessMapper.chess_to_sensor(self.gui.last_move_to)
                            if from_sensor is not None:
                                self.leds.set_led(from_sensor, 100, 100, 100, 0)  # Wit
                            if to_sensor is not None:
                                self.leds.set_led(to_sensor, 100, 100, 100, 0)  # Wit
                        
                        self.leds.show()
                    else:
                        self.leds.clear()
                        
                        # Toon laatste zet ook tijdens "uit" fase van knipperen
                        if hasattr(self.gui, 'last_move_from') and self.gui.last_move_from and self.gui.last_move_to:
                            from_sensor = ChessMapper.chess_to_sensor(self.gui.last_move_from)
                            to_sensor = ChessMapper.chess_to_sensor(self.gui.last_move_to)
                            if from_sensor is not None:
                                self.leds.set_led(from_sensor, 100, 100, 100, 0)  # Wit
                            if to_sensor is not None:
                                self.leds.set_led(to_sensor, 100, 100, 100, 0)  # Wit
                        
                        self.leds.show()
                    
                    # Update blink state
                    self.last_blink_state = blink_on
                    return  # Skip andere LED updates bij checkmate
            
            # Reset blink state als er geen selectie is
            if self.last_blink_state is not None:
                self.last_blink_state = None
                self.leds.clear()
                
                # Toon laatste zet in dim wit (als die bestaat)
                if hasattr(self.gui, 'last_move_from') and self.gui.last_move_from and self.gui.last_move_to:
                    from_sensor = ChessMapper.chess_to_sensor(self.gui.last_move_from)
                    to_sensor = ChessMapper.chess_to_sensor(self.gui.last_move_to)
                    if from_sensor is not None:
                        self.leds.set_led(from_sensor, 30, 30, 30, 10)  # Dim wit
                    if to_sensor is not None:
                        self.leds.set_led(to_sensor, 30, 30, 30, 10)  # Dim wit
                    
                    # Toon ook intermediate squares in paars/magenta
                    if hasattr(self.gui, 'last_move_intermediate'):
                        for inter_pos in self.gui.last_move_intermediate:
                            inter_sensor = ChessMapper.chess_to_sensor(inter_pos)
                            if inter_sensor is not None:
                                self.leds.set_led(inter_sensor, 40, 0, 40, 0)  # Dim paars/magenta
                
                self.leds.show()
        
        # Board validation: rood knipperen voor mismatches
        # Als lijst leeg is maar er waren vorige mismatches, clear die LEDs en herstel last move
        if not self.board_mismatch_positions and self.previous_mismatch_positions:
            # Clear alle vorige mismatch LEDs
            for pos in self.previous_mismatch_positions:
                sensor_num = ChessMapper.chess_to_sensor(pos)
                if sensor_num is not None:
                    self.leds.set_led(sensor_num, 0, 0, 0, 0)
            
            # Herstel last move LEDs (dim wit)
            if hasattr(self.gui, 'last_move_from') and self.gui.last_move_from:
                from_sensor = ChessMapper.chess_to_sensor(self.gui.last_move_from)
                if from_sensor is not None:
                    self.leds.set_led(from_sensor, 30, 30, 30, 10)
            if hasattr(self.gui, 'last_move_to') and self.gui.last_move_to:
                to_sensor = ChessMapper.chess_to_sensor(self.gui.last_move_to)
                if to_sensor is not None:
                    self.leds.set_led(to_sensor, 30, 30, 30, 10)
            if hasattr(self.gui, 'last_move_intermediate'):
                for inter_pos in self.gui.last_move_intermediate:
                    inter_sensor = ChessMapper.chess_to_sensor(inter_pos)
                    if inter_sensor is not None:
                        self.leds.set_led(inter_sensor, 40, 0, 40, 0)
            
            self.leds.show()
            self.previous_mismatch_positions = []
            self.last_mismatch_blink_state = False  # Reset mismatch blink state
        elif self.board_mismatch_positions:
            blink_on = (pygame.time.get_ticks() // 500) % 2 == 0
            
            # Play sound effect when transitioning from off to on
            if blink_on and not self.last_mismatch_blink_state:
                self.sound_manager.play_mismatch()
            
            self.last_mismatch_blink_state = blink_on
            
            # Clear LEDs voor posities die niet meer in mismatch list zitten
            for pos in self.previous_mismatch_positions:
                if pos not in self.board_mismatch_positions:
                    sensor_num = ChessMapper.chess_to_sensor(pos)
                    if sensor_num is not None:
                        self.leds.set_led(sensor_num, 0, 0, 0, 0)
            
            # Zet rode LEDs voor huidige mismatches
            for pos in self.board_mismatch_positions:
                sensor_num = ChessMapper.chess_to_sensor(pos)
                if sensor_num is not None:
                    if blink_on:
                        # Rood knipperen voor elke mismatch (missing of extra piece)
                        self.leds.set_led(sensor_num, 255, 0, 0, 0)
                    else:
                        # Uit fase
                        self.leds.set_led(sensor_num, 0, 0, 0, 0)
            
            self.leds.show()
            self.previous_mismatch_positions = self.board_mismatch_positions.copy()
    
    def _handle_events(self, gui_result):
        """
        Handle pygame events
        
        Returns:
            Boolean - True om door te gaan, False om te stoppen
        """
        # Unpack GUI result
        ok_button = gui_result.get('ok_button')
        tabs = gui_result.get('tabs', {})
        sliders = gui_result.get('sliders', {})
        toggles = gui_result.get('toggles', {})
        exit_yes_button = gui_result.get('exit_yes')
        exit_no_button = gui_result.get('exit_no')
        new_game_normal_button = gui_result.get('new_game_normal')
        new_game_assisted_button = gui_result.get('new_game_assisted')
        new_game_cancel_button = gui_result.get('new_game_cancel')
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                # Reset activity timer (alleen als niet screensaver starting)
                if not self.screensaver_starting:
                    self.last_activity_time = time.time()
                self.screen_dirty = True  # Herteken bij keyboard events
                if event.key == pygame.K_ESCAPE:
                    if self.gui.show_settings:
                        self.gui.show_settings = False
                        self.gui.temp_settings = {}
                    elif hasattr(self.gui, 'show_promotion_dialog') and self.gui.show_promotion_dialog:
                        # Cancel promotion - blokkeer ESC tijdens promotion
                        pass
                    else:
                        return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Reset activity timer (alleen als niet screensaver starting)
                if not self.screensaver_starting:
                    self.last_activity_time = time.time()
                self.screen_dirty = True  # Herteken bij mouse events
                if event.button == 1:  # Left click
                    if not self._handle_mouse_click(event.pos, gui_result):
                        return False  # Exit game
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.gui.events.stop_slider_drag()
                    self.screen_dirty = True
            elif event.type == pygame.MOUSEMOTION:
                self.gui.events.handle_slider_drag(event.pos, sliders)
                self.screen_dirty = True  # Herteken bij mouse beweging
        
        return True
    
    def _handle_mouse_click(self, pos, gui_result):
        """
        Handle mouse click (dialog en board clicks)
        
        Returns:
            Boolean - True om door te gaan, False om te stoppen
        """
        # Unpack GUI components
        ok_button = gui_result.get('ok_button')
        tabs = gui_result.get('tabs', {})
        sliders = gui_result.get('sliders', {})
        toggles = gui_result.get('toggles', {})
        exit_yes_button = gui_result.get('exit_yes')
        exit_no_button = gui_result.get('exit_no')
        new_game_normal_button = gui_result.get('new_game_normal')
        new_game_assisted_button = gui_result.get('new_game_assisted')
        new_game_cancel_button = gui_result.get('new_game_cancel')
        stop_game_yes_button = gui_result.get('stop_game_yes')
        stop_game_no_button = gui_result.get('stop_game_no')
        skip_setup_yes_button = gui_result.get('skip_setup_yes')
        skip_setup_no_button = gui_result.get('skip_setup_no')
        undo_yes_button = gui_result.get('undo_yes')
        undo_no_button = gui_result.get('undo_no')
        
        # Check if tutorial is active and click is on board
        if self.tutorial_active:
            # Check if click is within board area (not on sidebar)
            # Board is on left side, sidebar on right
            board_width = self.screen.get_height()  # Board is square, height = width
            if pos[0] < board_width:
                print("Tutorial exit - board clicked")
                self.tutorial_active = False
                self.leds.clear()
                self.leds.show()
                # Clear tutorial squares from board
                self.gui.tutorial_squares = {}
                # Restart LED animator
                self.led_animator.start_random_animation()
                # Reset activity timer to prevent immediate screensaver
                self.last_activity_time = time.time()
                self.screen_dirty = True
                return True
        
        # Undo confirmation dialog
        if self.gui.show_undo_confirm:
            if undo_yes_button and undo_yes_button.collidepoint(pos):
                print("\nUndo confirmed, performing undo...")
                self._handle_undo()
                self.gui.show_undo_confirm = False
                self.screen_dirty = True
            elif undo_no_button and undo_no_button.collidepoint(pos):
                print("\nUndo cancelled")
                self.gui.show_undo_confirm = False
                self.screen_dirty = True
        
        # Skip setup step confirmation dialog
        elif self.gui.show_skip_setup_step_confirm:
            if self.gui.handle_skip_setup_yes_click(pos, skip_setup_yes_button):
                print("\nSkipping current setup step...")
                self._advance_setup_step()
            elif self.gui.handle_skip_setup_no_click(pos, skip_setup_no_button):
                pass  # Gewoon dialog sluiten en doorgaan met wachten
        
        # Promotion dialog
        elif hasattr(self.gui, 'show_promotion_dialog') and self.gui.show_promotion_dialog:
            promotion_buttons = gui_result.get('promotion_buttons', {})
            for piece_symbol, button_rect in promotion_buttons.items():
                if button_rect.collidepoint(pos):
                    print(f"\nPromotion choice: {piece_symbol.upper()}")
                    # Set promotion choice en probeer move opnieuw
                    self.gui.promotion_choice = piece_symbol
                    self.gui.show_promotion_dialog = False
                    
                    # Doe de move met promotion
                    from_pos = self.gui.promotion_from
                    to_pos = self.gui.promotion_to
                    
                    move_result = self.engine.make_move(from_pos, to_pos, promotion=piece_symbol)
                    
                    if isinstance(move_result, dict):
                        move_success = move_result.get('success', False)
                    else:
                        move_success = bool(move_result)
                    
                    if move_success:
                        print(f"  Promotion successful: {from_pos} -> {to_pos} = {piece_symbol.upper()}")
                        
                        # Mark game als gestart
                        self.game_started = True
                        self.last_activity_time = time.time()
                        
                        # Clear highlights en LEDs
                        self.gui.highlight_squares([])
                        self.gui.set_selected_piece(None, None)
                        self.leds.clear()
                        self.leds.show()
                        
                        # Reset selectie EN promotion choice
                        self.selected_square = None
                        self.gui.promotion_choice = None
                        self.gui.promotion_from = None
                        self.gui.promotion_to = None
                        
                        # Update last move
                        if hasattr(self.gui, 'set_last_move'):
                            self.gui.set_last_move(from_pos, to_pos)
                        
                        # Check game status
                        if self.engine.is_game_over():
                            print(f"\n*** {self.engine.get_game_result()} ***\n")
                        else:
                            # Als VS Computer aan staat, laat computer zet doen
                            if self._is_vs_computer_enabled() and self.ai:
                                self.screen.fill(self.gui.COLOR_BG)
                                self.gui.draw_board()
                                self.gui.draw_pieces()
                                self.gui.draw_debug_overlays()
                                if self.gui.settings.get('show_coordinates', True):
                                    self.gui.draw_coordinates()
                                self.gui.draw_sidebar()
                                pygame.display.flip()
                                self.make_computer_move()
                    
                    self.screen_dirty = True
                    return True
        
        # Exit confirmation dialog
        elif self.gui.show_exit_confirm:
            if self.gui.handle_exit_yes_click(pos, exit_yes_button):
                print("\nExiting game...")
                return False
            elif self.gui.handle_exit_no_click(pos, exit_no_button):
                pass
        
        # New game confirmation dialog
        elif self.gui.show_new_game_confirm:
            if self.gui.handle_new_game_normal_click(pos, new_game_normal_button):
                print("\nStarting new game (normal setup)...")
                self.engine.reset()
                self.game_started = True  # Set to True to show "Stop Game" button
                self.last_activity_time = time.time()
                self.gui.show_new_game_confirm = False
                self._clear_selection()
                
                # Detecteer welke kleur rechts staat en roteer die
                self._update_rotated_color()
                
                # Stop LED animatie - spel is nu actief
                self.led_animator.stop()
                
                # Reset last move highlighting
                if hasattr(self.gui, 'set_last_move'):
                    self.gui.set_last_move(None, None)
                
                # Forceer LED clear (ook als er geen selectie was)
                self.leds.clear()
                self.leds.show()
                
                # Forceer screen redraw voor nieuwe button layout
                self.screen_dirty = True
                
            elif self.gui.handle_new_game_assisted_click(pos, new_game_assisted_button):
                print("\nStarting new game (assisted setup)...")
                self.engine.reset()
                self.game_started = False  # Blijft False tot setup compleet
                self.gui.show_new_game_confirm = False
                self._clear_selection()
                
                # Stop LED animatie - assisted setup neemt over
                self.led_animator.stop()
                
                # Start assisted setup
                self._start_assisted_setup()
                
            elif self.gui.handle_new_game_cancel_click(pos, new_game_cancel_button):
                pass
        
        # Stop game confirmation dialog
        elif self.gui.show_stop_game_confirm:
            if self.gui.handle_stop_game_yes_click(pos, stop_game_yes_button):
                print("\nStopping game...")
                self.engine.reset()
                self.game_started = False  # Reset game started state
                self.last_activity_time = time.time()  # Reset timer voor screensaver
                self.gui.show_stop_game_confirm = False
                self._clear_selection()
                
                # Reset last move highlighting
                if hasattr(self.gui, 'set_last_move'):
                    self.gui.set_last_move(None, None)
                
                # Start LED animatie - spel is nu idle
                self.led_animator.start_random_animation()
                
            elif self.gui.handle_stop_game_no_click(pos, stop_game_no_button):
                pass
        
        # Update status dialog
        elif self.gui.show_update_status_dialog:
            update_dialog_buttons = gui_result.get('update_dialog_buttons')
            if update_dialog_buttons:
                # OK button (for up_to_date, success, error)
                ok_button = update_dialog_buttons.get('ok_button')
                if ok_button and ok_button.collidepoint(pos):
                    self.gui.show_update_status_dialog = False
                    self.gui.update_info = {}
                    self.screen_dirty = True
                
                # Update button (for available)
                update_button = update_dialog_buttons.get('update_button')
                if update_button and update_button.collidepoint(pos):
                    print("Starting update...")
                    self._perform_update()
                
                # Cancel button (for available)
                cancel_button = update_dialog_buttons.get('cancel_button')
                if cancel_button and cancel_button.collidepoint(pos):
                    self.gui.show_update_status_dialog = False
                    self.gui.update_info = {}
                    self.screen_dirty = True
        
        # Settings dialog
        elif self.gui.show_settings:
            self._handle_settings_click(pos, gui_result)
        
        # Game board clicks
        else:
            self._handle_game_click(pos)
        
        return True
    
    def _handle_settings_click(self, pos, gui_result):
        """Handle clicks in settings dialog"""
        tabs = gui_result.get('tabs', {})
        sliders = gui_result.get('sliders', {})
        toggles = gui_result.get('toggles', {})
        ok_button = gui_result.get('ok_button')
        screensaver_button = gui_result.get('screensaver_button')
        test_position_button = gui_result.get('test_position_button')
        tutorial_button = gui_result.get('tutorial_button')
        check_updates_button = gui_result.get('check_updates_button')
        
        # Check updates button
        if check_updates_button and check_updates_button.collidepoint(pos):
            print("Checking for updates...")
            self.gui.show_settings = False
            self.gui.temp_settings = {}
            self._check_for_updates()
            return
        
        # Check test position button (chess only)
        if test_position_button and test_position_button.collidepoint(pos):
            self._load_test_position()
            self.gui.show_settings = False
            self.gui.temp_settings = {}
            return
        
        # Check tutorial button
        if tutorial_button and tutorial_button.collidepoint(pos):
            print("Starting tutorial mode...")
            self.tutorial_active = True
            self.tutorial_time = 0
            self.tutorial_step = 0
            # Stop LED animator
            self.led_animator.stop()
            # Clear any existing LED effects
            self.leds.clear()
            self.leds.show()
            # Show first tutorial step (row 1)
            self._show_tutorial_row(1)
            # Reset LED animation state
            if hasattr(self, '_ai_move_leds_set'):
                self._ai_move_leds_set = False
            if hasattr(self, '_castling_leds_set'):
                self._castling_leds_set = False
            self.gui.show_settings = False
            self.gui.temp_settings = {}
            self.screen_dirty = True
            return
        
        # Check screensaver button
        if screensaver_button and screensaver_button.collidepoint(pos):
            self.screensaver_starting = True
            self.screensaver_start_time = time.time()
            self.gui.show_settings = False
            self.gui.temp_settings = {}
            return
        
        # Tab clicks
        if self.gui.events.handle_tab_click(pos, tabs):
            return
        
        # Toggle clicks
        if self.gui.events.handle_toggle_click(pos, toggles.get('coordinates')):
            return
        if self.gui.events.handle_vs_computer_toggle_click(pos, toggles.get('vs_computer')):
            return
        if self.gui.events.handle_strict_touch_move_toggle_click(pos, toggles.get('strict_touch_move')):
            return
        if self.gui.events.handle_use_worstfish_toggle_click(pos, toggles.get('use_worstfish')):
            return
        if self.gui.events.handle_validate_board_state_toggle_click(pos, toggles.get('validate_board_state')):
            return
        if self.gui.events.handle_screensaver_audio_toggle_click(pos, toggles.get('screensaver_audio')):
            return
        if self.gui.events.handle_debug_toggle_click(pos, toggles.get('debug_sensors')):
            return
        # Checkers toggles
        if self.gui.events.handle_vs_computer_checkers_toggle_click(pos, toggles.get('vs_computer_checkers')):
            return
        if self.gui.events.handle_strict_touch_move_checkers_toggle_click(pos, toggles.get('strict_touch_move_checkers')):
            return
        
        # Screensaver button (debug tab)
        if screensaver_button:
            if screensaver_button.collidepoint(pos):
                print("Screensaver start over 500ms...")
                self.screensaver_starting = True
                self.screensaver_start_time = time.time()
                self.gui.show_settings = False
                self.gui.temp_settings = {}
                return
        
        # Power profile dropdown
        if self.gui.show_power_dropdown and self.gui.events.handle_power_profile_item_click(
            pos, gui_result.get('dropdown_items', [])):
            return
        if self.gui.events.handle_power_profile_dropdown_click(
            pos, gui_result.get('dropdowns', {}).get('power_profile')):
            return
        
        # Slider clicks
        if self.gui.events.handle_brightness_slider_click(pos, sliders.get('brightness')):
            return
        if self.gui.events.handle_skill_slider_click(pos, sliders.get('skill')):
            return
        if self.gui.events.handle_think_time_slider_click(pos, sliders.get('think_time')):
            return
        if self.gui.events.handle_depth_slider_click(pos, sliders.get('depth')):
            return
        # Checkers AI sliders
        if self.gui.events.handle_ai_difficulty_slider_click(pos, sliders.get('ai_difficulty')):
            return
        if self.gui.events.handle_ai_think_time_slider_click(pos, sliders.get('ai_think_time')):
            return
        
        # OK button
        if self.gui.handle_ok_click(pos, ok_button):
            return
    
    def _handle_undo(self):
        """Maak laatste zet(ten) ongedaan"""
        # Clear selectie eerst
        self._clear_selection()
        
        # Check of VS Computer aan staat
        vs_computer = self._is_vs_computer_enabled()
        
        if vs_computer:
            # Tegen computer: maak 2 zetten ongedaan (computer + speler)
            if self.engine.undo_move():
                print("Undo: Computer zet ongedaan gemaakt")
                if self.engine.undo_move():
                    print("Undo: Speler zet ongedaan gemaakt")
                    self.show_temp_message("Undo: 2 moves back", duration=2000)
                else:
                    print("Waarschuwing: Kon speler zet niet ongedaan maken")
                    self.show_temp_message("Undo: 1 move back", duration=2000)
            else:
                print("Geen zetten om ongedaan te maken")
                self.show_temp_message("No moves to undo", duration=2000)
        else:
            # Tegen menselijke speler: maak 1 zet ongedaan
            if self.engine.undo_move():
                print("Undo: Laatste zet ongedaan gemaakt")
                self.show_temp_message("Undo: 1 move back", duration=2000)
            else:
                print("Geen zetten om ongedaan te maken")
                self.show_temp_message("No moves to undo", duration=2000)
        
        # Clear old last move LEDs first (before updating to new last move)
        if hasattr(self.gui, 'last_move_from') and self.gui.last_move_from:
            from_sensor = ChessMapper.chess_to_sensor(self.gui.last_move_from)
            if from_sensor is not None:
                self.leds.set_led(from_sensor, 0, 0, 0, 0)
        if hasattr(self.gui, 'last_move_to') and self.gui.last_move_to:
            to_sensor = ChessMapper.chess_to_sensor(self.gui.last_move_to)
            if to_sensor is not None:
                self.leds.set_led(to_sensor, 0, 0, 0, 0)
        if hasattr(self.gui, 'last_move_intermediate'):
            for inter_pos in self.gui.last_move_intermediate:
                inter_sensor = ChessMapper.chess_to_sensor(inter_pos)
                if inter_sensor is not None:
                    self.leds.set_led(inter_sensor, 0, 0, 0, 0)
        
        # Update last move display to show the new last move (after undo)
        if hasattr(self.engine, 'get_last_move_squares'):
            result = self.engine.get_last_move_squares()
            # Handle both old (2-tuple) and new (3-tuple) return formats
            from_square = result[0]
            to_square = result[1]
            intermediate = result[2] if len(result) > 2 else []
            
            if from_square and to_square:
                # Update GUI with new last move
                self.gui.set_last_move(from_square, to_square, intermediate)
                print(f"Updated last move display: {from_square} -> {to_square}")
                if intermediate:
                    print(f"  Intermediate (rook): {intermediate}")
                
                # Turn on new last move LEDs - koning in dim wit
                from_sensor = ChessMapper.chess_to_sensor(from_square)
                to_sensor = ChessMapper.chess_to_sensor(to_square)
                if from_sensor is not None:
                    self.leds.set_led(from_sensor, 30, 30, 30, 10)  # Dim wit
                if to_sensor is not None:
                    self.leds.set_led(to_sensor, 30, 30, 30, 10)  # Dim wit
                
                # Turn on intermediate LEDs - rook in magenta (zoals checkers intermediate)
                for inter_pos in intermediate:
                    inter_sensor = ChessMapper.chess_to_sensor(inter_pos)
                    if inter_sensor is not None:
                        self.leds.set_led(inter_sensor, 40, 0, 40, 0)  # Magenta
            else:
                # No moves left, clear last move display
                self.gui.last_move_from = None
                self.gui.last_move_to = None
                if hasattr(self.gui, 'last_move_intermediate'):
                    self.gui.last_move_intermediate = []
                print("Cleared last move display (no moves left)")
        
        # Update LEDs and display
        self.leds.show()
        self.screen_dirty = True
    
    def _handle_game_click(self, pos):
        """Handle clicks on game board"""
        # New Game / Stop Game button - disabled tijdens assisted setup
        # Maak hitbox groter als game niet gestart (button is dan volle breedte)
        new_game_hitbox = self.gui.new_game_button
        if not self.game_started:
            # Volle breedte hitbox voor "New Game" button
            new_game_hitbox = pygame.Rect(
                self.gui.new_game_button.x,
                self.gui.new_game_button.y,
                self.gui.new_game_button.width * 2 + 10,  # 2x breedte + spacing
                self.gui.new_game_button.height
            )
        
        if new_game_hitbox.collidepoint(pos):
            if self.gui.assisted_setup_mode:
                # Negeer klik tijdens setup
                return
            self._clear_selection()
            
            # Check of spel gestart is - zo ja, toon stop game dialog
            if self.game_started:
                self.gui.show_stop_game_confirm = True
            else:
                # Toon new game confirmation
                self.gui.show_new_game_confirm = True
            return
        
        # Undo button - alleen actief als spel gestart is
        if hasattr(self.gui, 'undo_button') and self.gui.undo_button.collidepoint(pos):
            if self.game_started:
                # Toon undo confirmation
                self.gui.show_undo_confirm = True
                self._clear_selection()
            return
        
        # Exit button
        if self.gui.handle_exit_click(pos):
            self._clear_selection()
            return
        
        # Settings button
        if self.gui.handle_settings_click(pos):
            self._clear_selection()
            self.temp_message = None
            return
        
        # Board click - verschillende modes
        clicked_square = self.gui.get_square_from_pos(pos)
        if clicked_square:
            # Assisted setup mode - toon confirmation dialog om te skippen
            if self.gui.assisted_setup_mode:
                self.gui.show_skip_setup_step_confirm = True
                return
            
            # Check of spel gestart is
            if not self.game_started:
                self.show_temp_message("Click 'New Game' to start playing!", duration=2000)
                return
            
            if self.selected_square:
                # Klik op hetzelfde veld?
                if clicked_square == self.selected_square:
                    strict_touch_move = self._is_strict_touch_move_enabled()
                    if strict_touch_move:
                        print(f"\nStrict touch-move: mag niet deselecteren door te klikken!")
                        self.show_temp_message("Cannot deselect - Touch-move rule!", duration=2000)
                    else:
                        print(f"\nDeselecteer {clicked_square}")
                        self._clear_selection()
                else:
                    # Probeer zet naar nieuw veld
                    self.handle_piece_added(clicked_square)
            else:
                # Selecteer stuk
                piece = self.engine.get_piece_at(clicked_square)
                if piece:
                    self.handle_piece_removed(clicked_square)
    
    def _clear_selection(self):
        """Clear piece selection en LEDs"""
        if self.selected_square:
            self.gui.highlight_squares([])
            self.gui.set_selected_piece(None, None)
            self.selected_square = None
            self.leds.clear()
            self.leds.show()
        
        # Clear AI move pending
        if self.ai_move_pending:
            self.ai_move_pending = None
            print("  ai_move_pending cleared")
        
        # Clear castling pending
        if self.castling_pending:
            self.castling_pending = None
            if hasattr(self, '_castling_leds_set'):
                self._castling_leds_set = False
            print("  castling_pending cleared")
    
    def cleanup(self):
        """Cleanup resources"""
        # Stop LED animator
        if hasattr(self, 'led_animator'):
            self.led_animator.stop()
        
        if self.ai:
            if hasattr(self.ai, 'cleanup'):
                self.ai.cleanup()
        self.leds.cleanup()
        self.sensors.cleanup()
        self.gui.quit()
        print(f"{self.__class__.__name__} afgesloten")
    
    def _start_assisted_setup(self):
        """Start assisted setup mode"""
        print("Starting assisted board setup...")
        self.gui.assisted_setup_mode = True
        self.gui.assisted_setup_step = 0
        self.gui.assisted_setup_waiting = True
        self.assisted_setup_placed_squares = set()  # Track welke squares al geplaatst zijn
        
        # Clear AI move pending
        self.ai_move_pending = None
        
        self._show_current_setup_step()
    
    def _get_setup_steps(self):
        """Get ordered list of piece setup steps (must be overridden by subclass)
        
        Returns:
            List of dicts: [{'name': str, 'squares': [str], 'color': tuple}, ...]
        """
        # Default: geen setup (moet door subclass worden geïmplementeerd)
        return []
    
    def _show_current_setup_step(self):
        """Show current step in assisted setup"""
        steps = self._get_setup_steps()
        
        if self.gui.assisted_setup_step >= len(steps):
            # Setup compleet
            self._finish_assisted_setup()
            return
        
        current_step = steps[self.gui.assisted_setup_step]
        print(f"Setup step {self.gui.assisted_setup_step + 1}/{len(steps)}: Place {current_step['name']}")
        
        # Update message met 2 regels
        message = [
            f"Place {current_step['name']}",
            "White on white LEDs, black on orange LEDs"
        ]
        self.show_temp_message(message, duration=99999)
        
        # Light up LEDs voor pieces die nog niet geplaatst zijn
        self.leds.clear()
        
        # White pieces
        for square in current_step.get('squares', []):
            if square not in self.assisted_setup_placed_squares:
                sensor_num = ChessMapper.chess_to_sensor(square)
                if sensor_num is not None:
                    r, g, b, w = current_step['color']
                    self.leds.set_led(sensor_num, r, g, b, w)
        
        # Black pieces (als aanwezig)
        if 'squares_black' in current_step:
            for square in current_step['squares_black']:
                if square not in self.assisted_setup_placed_squares:
                    sensor_num = ChessMapper.chess_to_sensor(square)
                    if sensor_num is not None:
                        r, g, b, w = current_step['color_black']
                        self.leds.set_led(sensor_num, r, g, b, w)
        
        self.leds.show()
        
        # Update GUI to highlight squares (alleen niet-geplaatste) - combineer wit en zwart
        all_squares = current_step.get('squares', []) + current_step.get('squares_black', [])
        remaining_squares = [sq for sq in all_squares if sq not in self.assisted_setup_placed_squares]
        self.gui.highlighted_squares = remaining_squares
        self.gui.capture_squares = []  # No captures during setup
        
        # Force screen update
        self.screen_dirty = True
    
    def _update_assisted_setup_sensors(self):
        """Check sensors during assisted setup and update LEDs"""
        if not self.gui.assisted_setup_mode:
            return
        
        steps = self._get_setup_steps()
        if self.gui.assisted_setup_step >= len(steps):
            return
        
        current_step = steps[self.gui.assisted_setup_step]
        current_sensors = self.read_sensors()
        
        # Combineer witte en zwarte squares
        all_squares_with_colors = []
        for square in current_step.get('squares', []):
            all_squares_with_colors.append((square, current_step['color']))
        for square in current_step.get('squares_black', []):
            all_squares_with_colors.append((square, current_step['color_black']))
        
        # Check welke pieces zijn toegevoegd of verwijderd
        pieces_added = False
        pieces_removed = False
        
        for square, color in all_squares_with_colors:
            is_detected = current_sensors.get(square, False)
            was_placed = square in self.assisted_setup_placed_squares
            
            if is_detected and not was_placed:
                # Nieuw stuk geplaatst
                self.assisted_setup_placed_squares.add(square)
                print(f"  Piece placed on {square}")
                
                # Turn off LED voor dit square
                sensor_num = ChessMapper.chess_to_sensor(square)
                if sensor_num is not None:
                    self.leds.set_led(sensor_num, 0, 0, 0, 0)
                pieces_added = True
                
            elif not is_detected and was_placed:
                # Stuk weggehaald
                self.assisted_setup_placed_squares.remove(square)
                print(f"  Piece removed from {square}")
                
                # Turn LED terug AAN voor dit square (met juiste kleur)
                sensor_num = ChessMapper.chess_to_sensor(square)
                if sensor_num is not None:
                    r, g, b, w = color
                    self.leds.set_led(sensor_num, r, g, b, w)
                pieces_removed = True
        
        # Update LEDs en GUI als er iets veranderd is
        if pieces_added or pieces_removed:
            self.leds.show()
            
            # Update highlighted squares (combineer witte en zwarte squares)
            all_step_squares = current_step.get('squares', []) + current_step.get('squares_black', [])
            remaining_squares = [sq for sq in all_step_squares if sq not in self.assisted_setup_placed_squares]
            self.gui.highlighted_squares = remaining_squares
            
            # Update message met 2 regels
            message = [
                f"Place {current_step['name']}",
                "White on white LEDs, black on orange LEDs"
            ]
            self.show_temp_message(message, duration=99999)
            
            # Force screen update
            self.screen_dirty = True
        
        # Check of ALLE pieces van deze stap geplaatst zijn - alleen bij toevoegingen checken
    
    def _update_tutorial(self, dt):
        """Update tutorial mode - cycle through rows, columns, and all diagonals"""
        self.tutorial_time += dt
        
        if self.tutorial_time >= self.tutorial_step_duration:
            self.tutorial_time = 0
            self.tutorial_step = (self.tutorial_step + 1) % 42  # 8 rows + 8 columns + 13 + 13 diagonals
            self.screen_dirty = True
            
            # Update LEDs only when step changes
            if self.tutorial_step < 8:
                # Show rows 1-8
                self._show_tutorial_row(self.tutorial_step + 1)
            elif self.tutorial_step < 16:
                # Show columns A-H
                col_idx = self.tutorial_step - 8
                self._show_tutorial_column(chr(ord('A') + col_idx))
            elif self.tutorial_step < 29:
                # Show diagonals going up-right (A1-H8 direction) - 13 diagonals (min length 2)
                diagonal_idx = self.tutorial_step - 16
                self._show_tutorial_diagonal_upright(diagonal_idx)
            else:
                # Show diagonals going down-right (A8-H1 direction) - 13 diagonals (min length 2)
                diagonal_idx = self.tutorial_step - 29
                self._show_tutorial_diagonal_downright(diagonal_idx)
    
    def _show_tutorial_row(self, row_num):
        """Show LEDs and board squares for a specific row (1-8)"""
        from lib.hardware.mapping import ChessMapper
        
        self.leds.clear()
        self.gui.tutorial_squares = {}
        
        # Light up all squares in this row
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            pos = f"{col}{row_num}"
            sensor = ChessMapper.chess_to_sensor(pos)
            if sensor is not None:
                # Cyan color for rows
                self.leds.set_led(sensor, 0, 255, 255, 0)
            # Add to board highlighting
            self.gui.tutorial_squares[pos] = (0, 255, 255)  # Cyan
        
        self.leds.show()
        self.screen_dirty = True
    
    def _show_tutorial_column(self, col):
        """Show LEDs and board squares for a specific column (A-H)"""
        from lib.hardware.mapping import ChessMapper
        
        self.leds.clear()
        self.gui.tutorial_squares = {}
        
        # Light up all squares in this column
        for row in range(1, 9):
            pos = f"{col}{row}"
            sensor = ChessMapper.chess_to_sensor(pos)
            if sensor is not None:
                # Cyan color for columns (same as rows)
                self.leds.set_led(sensor, 0, 255, 255, 0)
            # Add to board highlighting
            self.gui.tutorial_squares[pos] = (0, 255, 255)  # Cyan
        
        self.leds.show()
        self.screen_dirty = True
    
    def _show_tutorial_diagonal_upright(self, diagonal_idx):
        """Show LEDs and board squares for diagonals going up-right (/ direction) - starting from corners"""
        from lib.hardware.mapping import ChessMapper
        
        self.leds.clear()
        self.gui.tutorial_squares = {}
        
        # Generate diagonal squares starting from corners
        # First 7 diagonals: from left edge (column A), going from row 7 down to row 1
        # Next 6 diagonals: from bottom edge (row 1), going from column B to column G
        squares = []
        
        if diagonal_idx < 7:
            # Start from left column (A), rows 7,6,5,4,3,2,1
            start_row = 7 - diagonal_idx  # 7, 6, 5, 4, 3, 2, 1
            start_col = 0  # A
            for i in range(9 - start_row):  # length increases as we go down
                col = chr(ord('A') + start_col + i)
                row = start_row + i
                if col <= 'H' and row <= 8:
                    squares.append(f"{col}{row}")
        else:
            # Start from bottom row (row 1), columns B,C,D,E,F,G
            start_col = diagonal_idx - 7 + 1  # 1,2,3,4,5,6 -> B,C,D,E,F,G
            start_row = 1
            for i in range(8 - start_col):  # length decreases as we go right
                col = chr(ord('A') + start_col + i)
                row = start_row + i
                if col <= 'H' and row <= 8:
                    squares.append(f"{col}{row}")
        
        # Light up the diagonal
        for pos in squares:
            sensor = ChessMapper.chess_to_sensor(pos)
            if sensor is not None:
                # Cyan color for diagonals (same as rows)
                self.leds.set_led(sensor, 0, 255, 255, 0)
            # Add to board highlighting
            self.gui.tutorial_squares[pos] = (0, 255, 255)  # Cyan
        
        self.leds.show()
        self.screen_dirty = True
    
    def _show_tutorial_diagonal_downright(self, diagonal_idx):
        """Show LEDs and board squares for diagonals going down-right (\\ direction) - starting from corners"""
        from lib.hardware.mapping import ChessMapper
        
        self.leds.clear()
        self.gui.tutorial_squares = {}
        
        # Generate diagonal squares starting from corners
        # First 7 diagonals: from left edge (column A), going from row 2 up to row 8
        # Next 6 diagonals: from top edge (row 8), going from column B to column G
        squares = []
        
        if diagonal_idx < 7:
            # Start from left column (A), rows 2,3,4,5,6,7,8
            start_row = diagonal_idx + 2  # 2, 3, 4, 5, 6, 7, 8
            start_col = 0  # A
            for i in range(start_row):  # length increases as we go up
                col = chr(ord('A') + start_col + i)
                row = start_row - i
                if col <= 'H' and row >= 1:
                    squares.append(f"{col}{row}")
        else:
            # Start from top row (row 8), columns B,C,D,E,F,G
            start_col = diagonal_idx - 7 + 1  # 1,2,3,4,5,6 -> B,C,D,E,F,G
            start_row = 8
            for i in range(8 - start_col):  # length decreases as we go right
                col = chr(ord('A') + start_col + i)
                row = start_row - i
                if col <= 'H' and row >= 1:
                    squares.append(f"{col}{row}")
        
        # Light up the diagonal
        for pos in squares:
            sensor = ChessMapper.chess_to_sensor(pos)
            if sensor is not None:
                # Cyan color for diagonals (same as rows)
                self.leds.set_led(sensor, 0, 255, 255, 0)
            # Add to board highlighting
            self.gui.tutorial_squares[pos] = (0, 255, 255)  # Cyan
        
        self.leds.show()
        self.screen_dirty = True
    
    def _show_tutorial_diagonal(self, diagonal_type):
        """Show LEDs for diagonals (deprecated - kept for compatibility)"""
        from lib.hardware.mapping import ChessMapper
        
        self.leds.clear()
        
        if diagonal_type == 'main':
            # Main diagonal A1-H8
            for i in range(8):
                col = chr(ord('A') + i)
                row = i + 1
                pos = f"{col}{row}"
                sensor = ChessMapper.chess_to_sensor(pos)
                if sensor is not None:
                    # Yellow color for diagonals
                    self.leds.set_led(sensor, 0, 255, 255, 255)
        else:
            # Anti-diagonal A8-H1
            for i in range(8):
                col = chr(ord('A') + i)
                row = 8 - i
                pos = f"{col}{row}"
                sensor = ChessMapper.chess_to_sensor(pos)
                if sensor is not None:
                    # Yellow color for diagonals
                    self.leds.set_led(sensor, 0, 255, 255, 255)
        
        self.leds.show()
    
    def _draw_tutorial_overlay(self):
        """Draw simple tutorial instruction in sidebar"""
        if not self.tutorial_active:
            return
        
        # Get screen dimensions
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        board_size = screen_height  # Board is square
        sidebar_width = screen_width - board_size
        
        # Show exit instruction in sidebar center
        font = pygame.font.Font(None, 48)
        instruction = font.render("Click the board", True, (255, 255, 255))
        instruction2 = font.render("to exit tutorial", True, (255, 255, 255))
        
        # Center in sidebar
        sidebar_center_x = board_size + sidebar_width // 2
        sidebar_center_y = screen_height // 2
        
        instruction_rect = instruction.get_rect(center=(sidebar_center_x, sidebar_center_y - 30))
        instruction2_rect = instruction2.get_rect(center=(sidebar_center_x, sidebar_center_y + 30))
        
        # Dark background for text readability
        bg_rect = instruction_rect.union(instruction2_rect).inflate(40, 40)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))
        self.screen.blit(bg_surface, bg_rect.topleft)
        
        self.screen.blit(instruction, instruction_rect)
        self.screen.blit(instruction2, instruction2_rect)
    
    def _check_for_updates(self):
        """Check for updates by running update script in dry-run mode"""
        import subprocess
        import os
        
        # Show checking status
        self.gui.update_info = {
            'status': 'checking',
            'message': 'Checking for updates...',
            'details': []
        }
        self.gui.show_update_status_dialog = True
        self.screen_dirty = True
        
        # Force screen update to show dialog
        pygame.display.flip()
        
        try:
            # Get script directory
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            update_script = os.path.join(script_dir, 'update.sh')
            
            # Check if update script exists
            if not os.path.exists(update_script):
                self.gui.update_info = {
                    'status': 'error',
                    'message': 'Update script not found',
                    'details': ['Please ensure update.sh exists in the project root']
                }
                self.screen_dirty = True
                return
            
            # Run update script with check-only mode (just check, don't update)
            result = subprocess.run(
                ['/bin/bash', update_script, '--check-only'],
                cwd=script_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout + result.stderr
            print(f"Update check output:\n{output}")
            
            # Parse output
            # Exit code 0: up to date
            # Exit code 1: update available
            # Other: error
            if result.returncode == 0 and 'Already up to date' in output:
                # Extract version if available
                version = ''
                for line in output.split('\n'):
                    if 'version:' in line.lower():
                        # Extract version hash (first 7 chars)
                        parts = line.split(':')
                        if len(parts) > 1:
                            version = parts[1].strip()[:7]
                        break
                
                details = []
                if version:
                    details.append(f'Current version: {version}')
                details.append('You have the latest version installed')
                
                self.gui.update_info = {
                    'status': 'up_to_date',
                    'message': 'Your installation is up to date!',
                    'details': details
                }
            elif result.returncode == 1 and 'Update available' in output:
                # Extract version info
                versions = ''
                for line in output.split('\n'):
                    if 'Update available:' in line:
                        versions = line.split(':', 1)[1].strip()
                        break
                
                details = []
                if versions:
                    details.append(f'Version: {versions}')
                details.append('')
                details.append('Would you like to update now?')
                
                self.gui.update_info = {
                    'status': 'available',
                    'message': 'A new version is available!',
                    'details': details
                }
            else:
                # Error
                error_lines = [line.strip() for line in output.split('\n') if line.strip() and not line.startswith('#')][-3:]
                self.gui.update_info = {
                    'status': 'error',
                    'message': 'Update check failed',
                    'details': error_lines if error_lines else ['Unknown error occurred']
                }
                
        except subprocess.TimeoutExpired:
            self.gui.update_info = {
                'status': 'error',
                'message': 'Update check timed out',
                'details': ['Check your internet connection', 'and try again']
            }
        except Exception as e:
            self.gui.update_info = {
                'status': 'error',
                'message': 'Error checking for updates',
                'details': [str(e)]
            }
        
        self.screen_dirty = True
    
    def _perform_update(self):
        """Perform actual update"""
        import subprocess
        import os
        
        # Show updating status
        self.gui.update_info = {
            'status': 'checking',
            'message': 'Updating...',
            'details': ['Please wait while the update is being installed']
        }
        self.gui.show_update_status_dialog = True
        self.screen_dirty = True
        
        # Force screen update to show dialog
        pygame.display.flip()
        
        try:
            # Get script directory
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            update_script = os.path.join(script_dir, 'update.sh')
            
            # Run update script without --check-only (full update)
            result = subprocess.run(
                ['/bin/bash', update_script],
                cwd=script_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            output = result.stdout + result.stderr
            print(f"Update output:\n{output}")
            
            # Check if successful
            if result.returncode == 0 and 'Update completed successfully' in output:
                self.gui.update_info = {
                    'status': 'success',
                    'message': 'Update completed successfully!',
                    'details': [
                        'New version installed',
                        '',
                        'Please restart the application:',
                        '1. Exit the game',
                        '2. Run ./run.sh to start with new version'
                    ]
                }
            else:
                # Error
                error_lines = [line.strip() for line in output.split('\n') if line.strip() and not line.startswith('#')][-3:]
                self.gui.update_info = {
                    'status': 'error',
                    'message': 'Update failed',
                    'details': error_lines if error_lines else ['Unknown error occurred']
                }
                
        except subprocess.TimeoutExpired:
            self.gui.update_info = {
                'status': 'error',
                'message': 'Update timed out',
                'details': ['The update took too long', 'Please try again']
            }
        except Exception as e:
            self.gui.update_info = {
                'status': 'error',
                'message': 'Error performing update',
                'details': [str(e)]
            }
        
        self.screen_dirty = True
    
    def _advance_setup_step(self):
        """Advance to next setup step"""
        self.gui.assisted_setup_step += 1
        self._show_current_setup_step()
    
    def _finish_assisted_setup(self):
        """Finish assisted setup and start game"""
        print("Assisted setup complete! Starting game...")
        self.gui.assisted_setup_mode = False
        self.gui.assisted_setup_step = 0
        self.gui.assisted_setup_waiting = False
        self.game_started = True
        self.last_activity_time = time.time()
        self.temp_message = None
        
        # Detecteer welke kleur rechts staat en roteer die
        self._update_rotated_color()
        
        # Clear LEDs
        self.leds.clear()
        self.leds.show()
        
        # Clear highlights
        self.gui.highlighted_squares = []
        self.gui.capture_squares = []
        
        # Force screen update
        self.screen_dirty = True
