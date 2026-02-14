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
        self.screen_dirty = True  # Flag: herteken nodig (CPU optimalisatie)
        self.last_gui_result = {}  # Cache laatste gui_result voor button detection
        
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
        
        Returns:
            List van posities waar mismatch is (stuk zou er moeten zijn maar niet gedetecteerd)
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
                
                # Check screensaver status (ALLEEN als game NIET gestart EN NIET in assisted setup)
                if not self.game_started and not self.gui.assisted_setup_mode:
                    if not self.screensaver_active and not self.screensaver_starting and (current_time - self.last_activity_time) > self.screensaver_timeout:
                        # Start screensaver
                        self.screensaver_active = True
                        self.screensaver.start_audio()
                        self.leds.clear()
                        self.leds.show()
                        print("Screensaver gestart (timeout)")
                
                # Als game gestart is of assisted setup actief: zorg dat screensaver UIT is
                if self.game_started or self.gui.assisted_setup_mode:
                    if self.screensaver_active or self.screensaver_starting:
                        self.screensaver.stop_audio()
                        self.screensaver_active = False
                        self.screensaver_starting = False
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
                            print("Screensaver gestopt (touch)")
                    
                    # Check sensor changes om screensaver te stoppen
                    current_sensors = self.read_sensors()
                    added, removed = self.detect_changes(current_sensors, self.previous_sensor_state)
                    if added or removed:
                        self.screensaver.stop_audio()
                        self.screensaver_active = False
                        self.last_activity_time = current_time
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
                
                # Update LED blink animatie
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
                
                # Draw GUI alleen als screen dirty
                if self.screen_dirty:
                    gui_result = self.gui.draw(self.temp_message, self.temp_message_timer, game_started=self.game_started)
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
                # Alleen valideren als: spel gestart, setting enabled, EN geen actieve move
                if (self.game_started and 
                    not self.selected_square and 
                    not self.invalid_return_position and
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
        elif self.board_mismatch_positions:
            current_sensors = self.read_sensors()
            blink_on = (pygame.time.get_ticks() // 500) % 2 == 0
            
            for pos in self.board_mismatch_positions:
                # Check of magneet NU aanwezig is
                if current_sensors.get(pos, False):
                    # Magneet aanwezig: validatie zal volgende frame oplossen, zet uit
                    sensor_num = ChessMapper.chess_to_sensor(pos)
                    if sensor_num is not None:
                        self.leds.set_led(sensor_num, 0, 0, 0, 0)
                elif blink_on:
                    # Geen magneet: rood knipperen
                    sensor_num = ChessMapper.chess_to_sensor(pos)
                    if sensor_num is not None:
                        self.leds.set_led(sensor_num, 255, 0, 0, 0)
                else:
                    # Uit fase
                    sensor_num = ChessMapper.chess_to_sensor(pos)
                    if sensor_num is not None:
                        self.leds.set_led(sensor_num, 0, 0, 0, 0)
            
            self.leds.show()
            self.previous_mismatch_positions = self.board_mismatch_positions.copy()
        
        # Board validation: rood knipperen voor mismatches (altijd checken)
        if self.board_mismatch_positions:
            current_sensors = self.read_sensors()
            blink_on = (pygame.time.get_ticks() // 500) % 2 == 0
            
            for pos in self.board_mismatch_positions:
                # Check of magneet NU aanwezig is
                if current_sensors.get(pos, False):
                    # Magneet aanwezig: validatie zal volgende frame oplossen, zet uit
                    sensor_num = ChessMapper.chess_to_sensor(pos)
                    if sensor_num is not None:
                        self.leds.set_led(sensor_num, 0, 0, 0, 0)
                elif blink_on:
                    # Geen magneet: rood knipperen
                    sensor_num = ChessMapper.chess_to_sensor(pos)
                    if sensor_num is not None:
                        self.leds.set_led(sensor_num, 255, 0, 0, 0)
                else:
                    # Uit fase
                    sensor_num = ChessMapper.chess_to_sensor(pos)
                    if sensor_num is not None:
                        self.leds.set_led(sensor_num, 0, 0, 0, 0)
            
            self.leds.show()
    
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
        if self.gui.events.handle_threads_slider_click(pos, sliders.get('threads')):
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
        if pieces_added:
            all_step_squares = current_step.get('squares', []) + current_step.get('squares_black', [])
            all_placed = all(sq in self.assisted_setup_placed_squares for sq in all_step_squares)
            if all_placed:
                print(f"  All pieces for step {self.gui.assisted_setup_step + 1} detected!")
                self._advance_setup_step()
    
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
        
        # Clear LEDs
        self.leds.clear()
        self.leds.show()
        
        # Clear highlights
        self.gui.highlighted_squares = []
        self.gui.capture_squares = []
        
        # Force screen update
        self.screen_dirty = True
