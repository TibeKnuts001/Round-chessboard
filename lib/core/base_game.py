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
        self.game_paused = False  # Pause bij board mismatch
        self.previous_brightness = brightness
        self.temp_message = None  # Tijdelijke berichten
        self.temp_message_timer = 0  # Wanneer bericht verdwijnt
        self.last_blink_state = None  # Track LED blink state om onnodige updates te voorkomen
        
        # LED Animator voor idle effects
        self.led_animator = LEDAnimator(self.leds)
        self.led_animator.start_random_animation()  # Start animatie bij startup
        
        print(f"{self.__class__.__name__} klaar!")
    
    @abstractmethod
    def _create_engine(self):
        """
        Maak game-specifieke engine
        
        Returns:
            BaseEngine subclass instance (ChessEngine, CheckersEngine, etc.)
        """
        pass
    
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
        
        Args:
            sensor_state: Dict met posities en sensor states (True = stuk aanwezig)
        
        Returns:
            List van posities waar stukken zouden moeten zijn maar ontbreken
        """
        mismatches = []
        
        # Check alle velden op het bord
        for row in range(8):
            for col in range(8):
                pos = f"{chr(65 + col)}{8 - row}"
                
                # Wat zegt de engine?
                engine_has_piece = self.engine.get_piece_at(pos) is not None
                
                # Wat zegt de sensor?
                sensor_has_piece = sensor_state.get(pos, False)
                
                # Mismatch: engine denkt er staat een stuk, maar sensor detecteert niets
                if engine_has_piece and not sensor_has_piece:
                    mismatches.append(pos)
        
        return mismatches
    
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
                print("  Geen legal moves - stuk kan niet geselecteerd worden!")
                self.show_temp_message("No legal moves for this piece!", duration=2000)
        else:
            print("  Geen stuk op deze positie volgens engine")
    
    def handle_piece_added(self, position):
        """
        Handle wanneer stuk toegevoegd wordt
        
        Args:
            position: Positie notatie waar stuk neergezet is
        """
        print(f"\nStuk neergezet op {position}")
        
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
            
            # Probeer zet te maken
            move_result = self.engine.make_move(self.selected_square, position)
            
            # Parse result (kan bool of dict zijn)
            if isinstance(move_result, dict):
                move_success = move_result.get('success', False)
                move_intermediate = move_result.get('intermediate', [])
            else:
                move_success = bool(move_result)
                move_intermediate = []
            
            if move_success:
                print(f"  Zet: {self.selected_square} -> {position}")
                
                # Mark game als gestart na eerste zet
                self.game_started = True
                
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
                
                # Check game status
                if self.engine.is_game_over():
                    print(f"\n*** {self.engine.get_game_result()} ***\n")
                else:
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
                # Update brightness indien gewijzigd
                current_brightness = self.gui.settings.get('brightness', 20)
                if current_brightness != self.previous_brightness:
                    self.leds.set_brightness(current_brightness)
                    self.previous_brightness = current_brightness
                    print(f"Brightness aangepast naar {current_brightness}%")
                
                # Update AI status indien gewijzigd (game-specifiek)
                self._update_ai_status()
                
                # Update LED blink animatie
                self._update_led_animations()
                
                # Lees sensors
                current_sensors = self.read_sensors()
                
                # Valideer board state
                self._validate_board_if_enabled(current_sensors)
                
                # Update sensor debug visualisatie
                if self.gui.settings.get('debug_sensors', False):
                    self.gui.update_sensor_debug_states(current_sensors)
                
                # Clear temp message als timer verlopen is
                if self.temp_message and pygame.time.get_ticks() >= self.temp_message_timer:
                    self.temp_message = None
                
                # Draw GUI
                gui_result = self.gui.draw(self.temp_message, self.temp_message_timer)
                
                # Handle events
                running = self._handle_events(gui_result)
                
                # Detecteer sensor veranderingen (alleen als niet gepauzeerd)
                if not self.game_paused:
                    added, removed = self.detect_changes(current_sensors, self.previous_sensor_state)
                    if added or removed:
                        self.handle_sensor_changes(added, removed)
                
                # Update previous state
                self.previous_sensor_state = current_sensors.copy()
                
                # Control framerate
                clock.tick(30)  # 30 FPS
                
        except KeyboardInterrupt:
            print("\n\nGame gestopt")
        finally:
            self.cleanup()
    
    def _update_ai_status(self):
        """Update AI opponent status (game-specifiek, kan overridden worden)"""
        pass  # Default implementatie: geen AI updates
    
    def _update_led_animations(self):
        """Update LED blink animaties voor geselecteerd veld en warnings"""
        if self.selected_square:
            # Bereken knipperstaat (500ms aan, 500ms uit)
            blink_on = (pygame.time.get_ticks() // 500) % 2 == 0
            
            # Alleen updaten als blink state veranderd is (voorkom flikkering)
            if blink_on == self.last_blink_state:
                return
            
            self.last_blink_state = blink_on
            
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
                        normal_squares = getattr(self.gui, 'highlighted_squares', destinations)
                        
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
    
    def _validate_board_if_enabled(self, current_sensors):
        """Valideer board state als validatie enabled is"""
        if self.gui.settings.get('validate_board_state', True):
            if not self.selected_square:
                self.board_mismatch_positions = self.validate_board_state(current_sensors)
                
                if self.board_mismatch_positions:
                    # Game paused: laat missende stukken rood knipperen
                    self.game_paused = True
                    blink_on = (pygame.time.get_ticks() // 500) % 2 == 0
                    
                    if blink_on:
                        self.leds.clear()
                        for pos in self.board_mismatch_positions:
                            sensor_num = ChessMapper.chess_to_sensor(pos)
                            if sensor_num is not None:
                                self.leds.set_led(sensor_num, 255, 0, 0, 0)  # ROOD
                        self.leds.show()
                    else:
                        self.leds.clear()
                        self.leds.show()
                    
                    # Toon warning message
                    if not self.temp_message:
                        self.show_temp_message("Board mismatch!", duration=999999)
                else:
                    # Board OK
                    if self.game_paused:
                        self.game_paused = False
                        self.temp_message = None
        else:
            # Validatie uitgeschakeld - reset state
            if self.game_paused or self.board_mismatch_positions:
                self.game_paused = False
                self.board_mismatch_positions = []
                self.temp_message = None
    
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
        new_game_yes_button = gui_result.get('new_game_yes')
        new_game_no_button = gui_result.get('new_game_no')
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.gui.show_settings:
                        self.gui.show_settings = False
                        self.gui.temp_settings = {}
                    else:
                        return False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if not self._handle_mouse_click(event.pos, gui_result):
                        return False  # Exit game
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.gui.events.stop_slider_drag()
            elif event.type == pygame.MOUSEMOTION:
                self.gui.events.handle_slider_drag(event.pos, sliders)
        
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
        new_game_yes_button = gui_result.get('new_game_yes')
        new_game_no_button = gui_result.get('new_game_no')
        stop_game_yes_button = gui_result.get('stop_game_yes')
        stop_game_no_button = gui_result.get('stop_game_no')
        
        # Exit confirmation dialog
        if self.gui.show_exit_confirm:
            if self.gui.handle_exit_yes_click(pos, exit_yes_button):
                print("\nExiting game...")
                return False
            elif self.gui.handle_exit_no_click(pos, exit_no_button):
                pass
        
        # New game confirmation dialog
        elif self.gui.show_new_game_confirm:
            if self.gui.handle_new_game_yes_click(pos, new_game_yes_button):
                print("\nStarting new game...")
                self.engine.reset()
                self.game_started = True  # Set to True to show "Stop Game" button
                self.gui.show_new_game_confirm = False
                self._clear_selection()
                
                # Stop LED animatie - spel is nu actief
                self.led_animator.stop()
                
                # Reset last move highlighting
                if hasattr(self.gui, 'set_last_move'):
                    self.gui.set_last_move(None, None)
                
                # Forceer LED clear (ook als er geen selectie was)
                self.leds.clear()
                self.leds.show()
                
            elif self.gui.handle_new_game_no_click(pos, new_game_no_button):
                pass
        
        # Stop game confirmation dialog
        elif self.gui.show_stop_game_confirm:
            if self.gui.handle_stop_game_yes_click(pos, stop_game_yes_button):
                print("\nStopping game...")
                self.engine.reset()
                self.game_started = False  # Reset game started state
                self.gui.show_stop_game_confirm = False
                self._clear_selection()
                
                # Reset last move highlighting
                if hasattr(self.gui, 'set_last_move'):
                    self.gui.set_last_move(None, None)
                
                # Start LED animatie - spel is nu idle
                self.led_animator.start_random_animation()
                
            elif self.gui.handle_stop_game_no_click(pos, stop_game_no_button):
                pass
        
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
        if self.gui.events.handle_validate_board_state_toggle_click(pos, toggles.get('validate_board_state')):
            return
        if self.gui.events.handle_debug_toggle_click(pos, toggles.get('debug_sensors')):
            return
        # Checkers toggles
        if self.gui.events.handle_vs_computer_checkers_toggle_click(pos, toggles.get('vs_computer_checkers')):
            return
        if self.gui.events.handle_strict_touch_move_checkers_toggle_click(pos, toggles.get('strict_touch_move_checkers')):
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
        if self.gui.events.handle_threads_slider_click(pos, sliders.get('threads')):
            return
        
        # OK button
        if self.gui.handle_ok_click(pos, ok_button):
            return
    
    def _handle_game_click(self, pos):
        """Handle clicks on game board"""
        # New game button
        if self.gui.handle_new_game_click(pos):
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
        
        # Board click - alleen toestaan als game gestart is
        clicked_square = self.gui.get_square_from_pos(pos)
        if clicked_square:
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
