#!/usr/bin/env python3
"""
Chess Game - Integratie van Hall Sensors, LEDs, Chess Engine en GUI
"""

import pygame
import time
import chess
from lib.hardware.leds import LEDController
from lib.hardware.sensors import SensorReader
from lib.hardware.mapping import ChessMapper
from lib.chessengine import ChessEngine
from lib.chessgui import ChessGUI
from lib.stockfish import StockfishEngine


class ChessGame:
    """Main chess game met sensor integratie"""
    
    def __init__(self, brightness=128):
        """Initialiseer chess game"""
        print("Initialiseer Chess Game...")
        
        # Hardware
        self.leds = LEDController(brightness=brightness)
        self.sensors = SensorReader()
        
        # Chess engine
        self.engine = ChessEngine()
        
        # GUI
        self.gui = ChessGUI(self.engine)
        self.screen = self.gui.screen  # Voor snelle toegang bij hertekenen
        
        # Stockfish AI (start alleen als VS Computer aan staat)
        self.stockfish = None
        if self.gui.settings.get('play_vs_computer', False):
            skill = self.gui.settings.get('stockfish_skill_level', 10)
            threads = self.gui.settings.get('stockfish_threads', 1)
            depth = self.gui.settings.get('stockfish_depth', 15)
            self.stockfish = StockfishEngine(skill_level=skill, threads=threads, depth=depth)
        
        # State tracking
        self.previous_sensor_state = {}
        self.selected_square = None
        self.invalid_return_position = None  # Track when piece returned illegally (strict touch-move)
        self.board_mismatch_positions = []  # Positions where pieces should be but aren't (validation)
        self.game_paused = False  # Pause game when board validation fails
        self.previous_brightness = brightness
        self.temp_message = None  # Voor tijdelijke berichten
        self.temp_message_timer = 0  # Wanneer bericht verdwijnt
        
        print("Chess Game klaar!")
    
    def read_sensors(self):
        """Lees sensor state en converteer naar dict met chess posities"""
        sensor_values = self.sensors.read_all()
        
        # Inverse logica: LOW = magneet aanwezig (stuk staat er)
        active_sensors = {}
        for i in range(64):
            chess_pos = ChessMapper.sensor_to_chess(i)
            if chess_pos:
                # True = stuk staat op veld (sensor LOW)
                active_sensors[chess_pos] = not sensor_values[i]
        
        return active_sensors
    
    def validate_board_state(self, sensor_state):
        """
        Vergelijk fysieke board state met engine state
        
        Args:
            sensor_state: Dict met chess posities en sensor states (True = stuk aanwezig)
        
        Returns:
            List van posities waar stukken zouden moeten zijn maar ontbreken
        """
        mismatches = []
        
        # Check alle velden op het bord
        for row in range(8):
            for col in range(8):
                chess_pos = f"{chr(65 + col)}{8 - row}"
                
                # Wat zegt de engine?
                engine_has_piece = self.engine.get_piece_at(chess_pos) is not None
                
                # Wat zegt de sensor?
                sensor_has_piece = sensor_state.get(chess_pos, False)
                
                # Mismatch: engine denkt er staat een stuk, maar sensor detecteert niets
                if engine_has_piece and not sensor_has_piece:
                    mismatches.append(chess_pos)
        
        return mismatches
    
    def detect_changes(self, current_state, previous_state):
        """
        Detecteer veranderingen in sensor state
        
        Returns:
            (added, removed) - sets van chess posities
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
            added: Set van chess posities waar stukken zijn neergezet
            removed: Set van chess posities waar stukken zijn weggehaald
        """

        # TODO: Acties zijn tijdelijk uitgezet
        for pos in removed:
            print(f"[SENSOR EVENT] Stuk weggehaald van {pos}")
            self.handle_piece_removed(pos)
        for pos in added:
            print(f"[SENSOR EVENT] Stuk neergezet op {pos}")
            self.handle_piece_added(pos)
    
    def update_leds(self, positions, color=(255, 255, 255, 0)):
        """
        Light LEDs op specifieke posities
        
        Args:
            positions: List van chess notaties
            color: (r, g, b, w) tuple
        """
        # Clear all LEDs
        self.leds.clear()
        
        # Light up specified positions
        for pos in positions:
            sensor_num = ChessMapper.chess_to_sensor(pos)
            if sensor_num is not None:
                r, g, b, w = color
                self.leds.set_led(sensor_num, r, g, b, w)
        
        self.leds.show()
    
    def handle_piece_removed(self, position):
        """
        Handle wanneer stuk weggehaald wordt
        
        Args:
            position: Chess notatie van waar stuk weggehaald is
        """
        print(f"\nStuk weggehaald van {position}")
        
        # Check of we terugkomen van een invalid return (rood knipperen -> blauw knipperen)
        if self.invalid_return_position == position:
            print(f"  Terug opgepakt van ongeldige return positie - terug naar normaal blauw")
            self.invalid_return_position = None
            # Continue met normale selectie flow (blauw knipperen)
        
        # Check of er een stuk staat volgens chess engine
        piece = self.engine.get_piece_at(position)
        if piece:
            print(f"  Stuk: {piece.symbol()}")
            
            # Haal legal moves op
            legal_moves = self.engine.get_legal_moves_from(position)
            
            if legal_moves:
                print(f"  Legal moves: {', '.join(legal_moves)}")
                
                # Toon opgepakt stuk in GUI (alleen als er legal moves zijn)
                self.gui.set_selected_piece(piece, position)
                
                # Highlight legal move posities
                self.gui.highlight_squares(legal_moves)
                
                # Light up LEDs voor legal moves (blauw - normaal)
                self.update_leds(legal_moves, color=(0, 0, 255, 0))
                
                # Onthoud geselecteerd veld
                self.selected_square = position
            else:
                print("  Geen legal moves - stuk kan niet geselecteerd worden!")
                # Toon tijdelijk bericht
                self.show_temp_message("No legal moves for this piece!", duration=2000)
        else:
            print("  Geen stuk op deze positie volgens engine")
    
    def handle_piece_added(self, position):
        """
        Handle wanneer stuk toegevoegd wordt
        
        Args:
            position: Chess notatie waar stuk neergezet is
        """
        print(f"\nStuk neergezet op {position}")
        
        if self.selected_square:
            # Check of stuk teruggeplaatst wordt op originele positie
            if position == self.selected_square:
                # Check strict touch-move setting
                strict_touch_move = self.gui.settings.get('strict_touch_move', False)
                
                if strict_touch_move:
                    print(f"  Strict touch-move: stuk teruggeplaatst - ROOD knipperen!")
                    
                    # Track invalid return position (blink animatie in main loop zorgt voor rood)
                    self.invalid_return_position = position
                    
                    # Show warning message
                    self.show_temp_message("Cannot return piece - Touch-move rule!", duration=2000)
                    return
                else:
                    print(f"  Stuk teruggeplaatst op originele positie - deselecteer")
                    
                    # Clear highlights en LEDs (deselectie)
                    self.gui.highlight_squares([])
                    self.gui.set_selected_piece(None, None)
                    self.leds.clear()
                    self.leds.show()
                    
                    # Reset selectie
                    self.selected_square = None
                    return
            
            # Probeer zet te maken
            if self.engine.make_move(self.selected_square, position):
                print(f"  Zet: {self.selected_square} -> {position}")
                
                # Clear highlights en LEDs
                self.gui.highlight_squares([])
                self.gui.set_selected_piece(None, None)  # Clear selected piece in GUI
                self.leds.clear()
                self.leds.show()
                
                # Reset selectie
                self.selected_square = None
                
                # Check game status
                if self.engine.is_game_over():
                    print(f"\n*** {self.engine.get_game_result()} ***\n")
                else:
                    # Als VS Computer aan staat, laat computer zet doen
                    if self.gui.settings.get('play_vs_computer', False) and self.stockfish:
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
    
    def make_computer_move(self):
        """Laat computer (Stockfish) een zet doen"""
        print("\nComputer denkt...")
        
        # Toon "thinking" animatie terwijl Stockfish denkt
        import threading
        import time as time_module
        
        thinking_done = False
        best_move = None
        
        def get_stockfish_move():
            nonlocal best_move, thinking_done
            # Gebruik stockfish think_time setting
            think_time = self.gui.settings.get('stockfish_think_time', 1000)
            best_move = self.stockfish.get_best_move(self.engine.board, think_time_ms=think_time)
            thinking_done = True
        
        # Start Stockfish in aparte thread
        stockfish_thread = threading.Thread(target=get_stockfish_move)
        stockfish_thread.start()
        
        # Toon animatie terwijl we wachten
        clock = pygame.time.Clock()
        animation_frame = 0
        
        while not thinking_done:
            # Handle pygame events om freeze te voorkomen
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    thinking_done = True
                    break
            
            # Herteken GUI met thinking indicator
            self.screen.fill(self.gui.COLOR_BG)
            self.gui.draw_board()
            self.gui.draw_pieces()
            self.gui.draw_debug_overlays()
            if self.gui.settings.get('show_coordinates', True):
                self.gui.draw_coordinates()
            self.gui.draw_sidebar()
            
            # Teken "thinking" overlay
            self._draw_thinking_indicator(animation_frame)
            
            pygame.display.flip()
            animation_frame += 1
            clock.tick(30)  # 30 FPS voor smooth animatie
        
        # Wacht tot thread klaar is
        stockfish_thread.join()
        
        if best_move:
            from_square = chess.square_name(best_move.from_square)
            to_square = chess.square_name(best_move.to_square)
            
            print(f"Computer zet: {from_square} -> {to_square}")
            
            # Maak de zet
            self.engine.board.push(best_move)
            
            # Check game status
            if self.engine.is_game_over():
                print(f"\n*** {self.engine.get_game_result()} ***\n")
    
    def _draw_thinking_indicator(self, frame):
        """Teken thinking indicator overlay"""
        # Grote overlay in het midden van het bord
        board_width = 800
        overlay_width = 300
        overlay_height = 120
        overlay_x = (board_width - overlay_width) // 2
        overlay_y = 300
        
        # Achtergrond box (solid, geen alpha)
        pygame.draw.rect(self.screen, (40, 40, 40), 
                        (overlay_x, overlay_y, overlay_width, overlay_height), 
                        border_radius=15)
        
        # Border (dikker en helderder)
        pygame.draw.rect(self.screen, (100, 200, 255), 
                        (overlay_x, overlay_y, overlay_width, overlay_height), 5, border_radius=15)
        
        # "Thinking..." tekst (groter)
        font = pygame.font.Font(None, 36)
        text = font.render("Computer thinking...", True, (255, 255, 255))
        text_rect = text.get_rect(center=(overlay_x + overlay_width // 2, overlay_y + 40))
        self.screen.blit(text, text_rect)
        
        # Rotating spinner (3 grotere dots die pulsen)
        dot_y = overlay_y + 80
        dot_spacing = 30
        center_x = overlay_x + overlay_width // 2
        
        for i in range(3):
            dot_x = center_x - dot_spacing + (i * dot_spacing)
            # Pulserende grootte gebaseerd op frame
            pulse = abs(((frame + i * 10) % 60) - 30) / 30.0  # 0.0 to 1.0
            radius = int(6 + pulse * 6)  # 6 tot 12 pixels
            
            # Teken dot (solid color, geen alpha)
            color_intensity = int(100 + pulse * 155)
            pygame.draw.circle(self.screen, (color_intensity, color_intensity, 255), (dot_x, dot_y), radius)
    
    def show_temp_message(self, message, duration=2000):
        """Toon tijdelijk bericht op scherm"""
        self.temp_message = message
        self.temp_message_timer = pygame.time.get_ticks() + duration
    
    def _draw_temp_message(self, message):
        """Teken tijdelijk bericht overlay"""
        # Kleinere overlay boven in het midden
        board_width = 800
        overlay_width = 350
        overlay_height = 80
        overlay_x = (board_width - overlay_width) // 2
        overlay_y = 50
        
        # Achtergrond box (donkerrood/oranje voor waarschuwing)
        pygame.draw.rect(self.screen, (80, 40, 20), 
                        (overlay_x, overlay_y, overlay_width, overlay_height), 
                        border_radius=12)
        
        # Border (oranje)
        pygame.draw.rect(self.screen, (255, 150, 0), 
                        (overlay_x, overlay_y, overlay_width, overlay_height), 4, border_radius=12)
        
        # Warning icon (!)
        font_large = pygame.font.Font(None, 48)
        icon = font_large.render("⚠", True, (255, 200, 0))
        icon_rect = icon.get_rect(center=(overlay_x + 30, overlay_y + overlay_height // 2))
        self.screen.blit(icon, icon_rect)
        
        # Message tekst
        font = pygame.font.Font(None, 26)
        text = font.render(message, True, (255, 255, 255))
        text_rect = text.get_rect(center=(overlay_x + overlay_width // 2 + 10, overlay_y + overlay_height // 2))
        self.screen.blit(text, text_rect)
    
    def run(self):
        """Main game loop"""
        print("\n" + "=" * 50)
        print("Chess Game Started")
        print("=" * 50)
        print("Druk op ESC of sluit venster om te stoppen\n")
        
        clock = pygame.time.Clock()
        running = True
        
        # Initiële sensor state
        current_sensors = self.read_sensors()
        self.previous_sensor_state = current_sensors.copy()
        
        try:
            while running:
                # Check en update brightness indien gewijzigd
                current_brightness = self.gui.settings.get('brightness', 20)
                if current_brightness != self.previous_brightness:
                    self.leds.set_brightness(current_brightness)
                    self.previous_brightness = current_brightness
                    print(f"Brightness aangepast naar {current_brightness}%")
                
                # Check en update Stockfish status indien gewijzigd
                vs_computer_enabled = self.gui.settings.get('play_vs_computer', False)
                stockfish_skill = self.gui.settings.get('stockfish_skill_level', 10)
                stockfish_threads = self.gui.settings.get('stockfish_threads', 1)
                stockfish_depth = self.gui.settings.get('stockfish_depth', 15)
                
                if vs_computer_enabled and not self.stockfish:
                    print(f"Starting Stockfish engine (skill {stockfish_skill}, threads {stockfish_threads}, depth {stockfish_depth})...")
                    self.stockfish = StockfishEngine(
                        skill_level=stockfish_skill,
                        threads=stockfish_threads,
                        depth=stockfish_depth
                    )
                    # Als stockfish niet kon starten, zet setting terug uit
                    if self.stockfish and not self.stockfish.process:
                        print("Stockfish kon niet starten - VS Computer mode uitgeschakeld")
                        self.gui.settings.set('play_vs_computer', False)
                        self.stockfish = None
                elif not vs_computer_enabled and self.stockfish:
                    print("Stopping Stockfish engine...")
                    self.stockfish.cleanup()
                    self.stockfish = None
                elif vs_computer_enabled and self.stockfish:
                    # Update parameters als die veranderd zijn
                    params_changed = False
                    
                    if hasattr(self.stockfish, 'skill_level') and self.stockfish.skill_level != stockfish_skill:
                        print(f"Updating Stockfish skill level to {stockfish_skill}...")
                        self.stockfish.skill_level = stockfish_skill
                        self.stockfish._send_command(f"setoption name Skill Level value {stockfish_skill}")
                        params_changed = True
                    
                    if hasattr(self.stockfish, 'threads') and self.stockfish.threads != stockfish_threads:
                        print(f"Updating Stockfish threads to {stockfish_threads}...")
                        self.stockfish.threads = stockfish_threads
                        self.stockfish._send_command(f"setoption name Threads value {stockfish_threads}")
                        params_changed = True
                    
                    if hasattr(self.stockfish, 'depth') and self.stockfish.depth != stockfish_depth:
                        print(f"Updating Stockfish depth to {stockfish_depth}...")
                        self.stockfish.depth = stockfish_depth
                        # Depth wordt gebruikt in get_best_move(), geen UCI command nodig
                        params_changed = True
                
                # Update knipperende LED voor geselecteerd veld
                if self.selected_square:
                    # Bereken knipperstaat (500ms aan, 500ms uit - sync met GUI)
                    blink_on = (pygame.time.get_ticks() // 500) % 2 == 0
                    
                    # Check of we in invalid return state zitten (strict touch-move violation)
                    if self.invalid_return_position:
                        # ROOD knipperen alleen voor originele positie, groen voor legal moves
                        if blink_on:
                            # Zet originele positie rood, legal moves groen
                            sensor_num = ChessMapper.chess_to_sensor(self.selected_square)
                            if sensor_num is not None:
                                self.leds.clear()
                                self.leds.set_led(sensor_num, 255, 0, 0, 0)  # ROOD voor originele positie
                                # Toon legal moves in groen
                                legal_moves = self.engine.get_legal_moves_from(self.selected_square)
                                for pos in legal_moves:
                                    move_sensor = ChessMapper.chess_to_sensor(pos)
                                    if move_sensor is not None:
                                        self.leds.set_led(move_sensor, 0, 255, 0, 0)  # GROEN voor legal moves
                                self.leds.show()
                        else:
                            # Alleen legal moves tonen (groen), originele positie uit
                            self.leds.clear()
                            legal_moves = self.engine.get_legal_moves_from(self.selected_square)
                            for pos in legal_moves:
                                move_sensor = ChessMapper.chess_to_sensor(pos)
                                if move_sensor is not None:
                                    self.leds.set_led(move_sensor, 0, 255, 0, 0)  # GROEN
                            self.leds.show()
                    else:
                        # Normaal blauw/groen knipperen
                        if blink_on:
                            # Zet geselecteerd veld blauw
                            sensor_num = ChessMapper.chess_to_sensor(self.selected_square)
                            if sensor_num is not None:
                                self.leds.clear()
                                self.leds.set_led(sensor_num, 0, 0, 255, 0)  # Blauw
                                # Toon ook nog steeds de legal moves in groen
                                legal_moves = self.engine.get_legal_moves_from(self.selected_square)
                                for pos in legal_moves:
                                    move_sensor = ChessMapper.chess_to_sensor(pos)
                                    if move_sensor is not None:
                                        self.leds.set_led(move_sensor, 0, 255, 0, 0)  # Groen
                                self.leds.show()
                        else:
                            # Alleen legal moves tonen (groen)
                            self.leds.clear()
                            legal_moves = self.engine.get_legal_moves_from(self.selected_square)
                            for pos in legal_moves:
                                move_sensor = ChessMapper.chess_to_sensor(pos)
                                if move_sensor is not None:
                                    self.leds.set_led(move_sensor, 0, 255, 0, 0)  # Groen
                            self.leds.show()
                
                # Lees sensors éénmalig per loop
                current_sensors = self.read_sensors()
                
                # Valideer board state (alleen als niet in selectie modus en validatie aan staat)
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
                                self.temp_message = None  # Clear mismatch message
                else:
                    # Validatie is uitgeschakeld - reset state
                    if self.game_paused or self.board_mismatch_positions:
                        self.game_paused = False
                        self.board_mismatch_positions = []
                        self.temp_message = None  # Clear mismatch message
                
                # Update sensor debug visualisatie als debug mode aan staat
                if self.gui.settings.get('debug_sensors', False):
                    self.gui.update_sensor_debug_states(current_sensors)
                
                # Clear temp message als timer verlopen is
                if self.temp_message and pygame.time.get_ticks() >= self.temp_message_timer:
                    self.temp_message = None
                
                # Draw GUI (inclusief temp message)
                gui_result = self.gui.draw(self.temp_message, self.temp_message_timer)
                ok_button = gui_result.get('ok_button')
                tabs = gui_result.get('tabs', {})
                sliders = gui_result.get('sliders', {})
                toggles = gui_result.get('toggles', {})
                exit_yes_button = gui_result.get('exit_yes')
                exit_no_button = gui_result.get('exit_no')
                new_game_yes_button = gui_result.get('new_game_yes')
                new_game_no_button = gui_result.get('new_game_no')
                
                # Handle pygame events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            # Als settings open is, sluit zonder opslaan
                            if self.gui.show_settings:
                                self.gui.show_settings = False
                                self.gui.temp_settings = {}  # Gooi temp settings weg
                            else:
                                running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 1:  # Left click
                            # Check exit confirmation dialog
                            if self.gui.show_exit_confirm:
                                # Check Yes klik
                                if self.gui.handle_exit_yes_click(event.pos, exit_yes_button):
                                    print("\nExiting game...")
                                    running = False
                                # Check No klik
                                elif self.gui.handle_exit_no_click(event.pos, exit_no_button):
                                    pass  # Dialog gesloten
                            # Check new game confirmation dialog
                            elif self.gui.show_new_game_confirm:
                                # Check Yes klik
                                if self.gui.handle_new_game_yes_click(event.pos, new_game_yes_button):
                                    print("\nStarting new game...")
                                    self.engine.reset()
                                    self.gui.show_new_game_confirm = False
                                    # Clear selection
                                    if self.selected_square:
                                        self.gui.highlight_squares([])
                                        self.gui.set_selected_piece(None, None)
                                        self.selected_square = None
                                    # Clear LEDs
                                    self.leds.clear()
                                    self.leds.show()
                                # Check No klik
                                elif self.gui.handle_new_game_no_click(event.pos, new_game_no_button):
                                    pass  # Dialog gesloten
                            # Check settings dialog
                            elif self.gui.show_settings:
                                # Check tab clicks
                                if self.gui.events.handle_tab_click(event.pos, tabs):
                                    pass  # Tab switched
                                # Check toggle klik (coordinates)
                                elif self.gui.events.handle_toggle_click(event.pos, toggles.get('coordinates')):
                                    pass  # Toggle getoggled
                                # Check VS Computer toggle
                                elif self.gui.events.handle_vs_computer_toggle_click(event.pos, toggles.get('vs_computer')):
                                    pass  # VS Computer toggle switched
                                # Check strict touch-move toggle
                                elif self.gui.events.handle_strict_touch_move_toggle_click(event.pos, toggles.get('strict_touch_move')):
                                    pass  # Strict touch-move toggle switched
                                # Check validate board state toggle
                                elif self.gui.events.handle_validate_board_state_toggle_click(event.pos, toggles.get('validate_board_state')):
                                    pass  # Validate board state toggle switched
                                # Check debug toggle
                                elif self.gui.events.handle_debug_toggle_click(event.pos, toggles.get('debug_sensors')):
                                    pass  # Debug toggle switched
                                # Check power profile dropdown items FIRST (if dropdown is open)
                                elif self.gui.show_power_dropdown and self.gui.events.handle_power_profile_item_click(
                                    event.pos,
                                    gui_result.get('dropdown_items', [])):
                                    pass  # Item selected
                                # Check power profile dropdown button (open/close)
                                elif self.gui.events.handle_power_profile_dropdown_click(
                                    event.pos, 
                                    gui_result.get('dropdowns', {}).get('power_profile')):
                                    pass  # Dropdown toggled
                                # Check brightness slider klik (start drag)
                                elif self.gui.events.handle_brightness_slider_click(event.pos, sliders.get('brightness')):
                                    pass  # Slider drag gestart
                                # Check stockfish skill slider klik (start drag)
                                elif self.gui.events.handle_skill_slider_click(event.pos, sliders.get('skill')):
                                    pass  # Stockfish slider drag gestart
                                # Stockfish think time slider
                                elif self.gui.events.handle_think_time_slider_click(event.pos, sliders.get('think_time')):
                                    pass
                                # Stockfish depth slider
                                elif self.gui.events.handle_depth_slider_click(event.pos, sliders.get('depth')):
                                    pass
                                # Stockfish threads slider
                                elif self.gui.events.handle_threads_slider_click(event.pos, sliders.get('threads')):
                                    pass
                                # Check OK klik
                                elif self.gui.handle_ok_click(event.pos, ok_button):
                                    pass  # Dialog gesloten
                            else:
                                # Check new game button
                                if self.gui.handle_new_game_click(event.pos):
                                    # Clear selection when opening new game dialog
                                    if self.selected_square:
                                        self.gui.highlight_squares([])
                                        self.gui.set_selected_piece(None, None)
                                        self.selected_square = None
                                        self.leds.clear()
                                        self.leds.show()
                                # Check exit button
                                elif self.gui.handle_exit_click(event.pos):
                                    # Clear selection when opening exit dialog
                                    if self.selected_square:
                                        self.gui.highlight_squares([])
                                        self.gui.set_selected_piece(None, None)
                                        self.selected_square = None
                                        self.leds.clear()
                                        self.leds.show()
                                # Check settings button
                                elif self.gui.handle_settings_click(event.pos):
                                    # Settings opened - clear any selection
                                    if self.selected_square:
                                        self.gui.highlight_squares([])
                                        self.gui.set_selected_piece(None, None)
                                        self.selected_square = None
                                        self.leds.clear()
                                        self.leds.show()
                                    # Clear temp message (board mismatch warning)
                                    self.temp_message = None
                                else:
                                    # Check board click
                                    clicked_square = self.gui.get_square_from_pos(event.pos)
                                    if clicked_square:
                                        # Als er al een stuk geselecteerd is
                                        if self.selected_square:
                                            # Klik op hetzelfde veld? Deselecteer
                                            if clicked_square == self.selected_square:
                                                # Check strict touch-move setting
                                                strict_touch_move = self.gui.settings.get('strict_touch_move', False)
                                                
                                                if strict_touch_move:
                                                    print(f"\nStrict touch-move: mag niet deselecteren door te klikken!")
                                                    self.show_temp_message("Cannot deselect - Touch-move rule!", duration=2000)
                                                else:
                                                    print(f"\nDeselecteer {clicked_square}")
                                                    self.gui.highlight_squares([])
                                                    self.gui.set_selected_piece(None, None)
                                                    self.selected_square = None
                                                    self.leds.clear()
                                                    self.leds.show()
                                            else:
                                                # Probeer zet te maken naar nieuw veld
                                                self.handle_piece_added(clicked_square)
                                        else:
                                            # Selecteer stuk op deze positie
                                            piece = self.engine.get_piece_at(clicked_square)
                                            if piece:
                                                self.handle_piece_removed(clicked_square)
                    elif event.type == pygame.MOUSEBUTTONUP:
                        if event.button == 1:  # Left click released
                            self.gui.events.stop_slider_drag()
                    elif event.type == pygame.MOUSEMOTION:
                        # Handle slider drags
                        self.gui.events.handle_slider_drag(event.pos, sliders)
                
                # Detecteer sensor veranderingen (current_sensors al gelezen eerder in loop)
                # Alleen als game niet gepauzeerd is door board validation
                if not self.game_paused:
                    added, removed = self.detect_changes(current_sensors, self.previous_sensor_state)
                    
                    # Handle sensor events
                    if added or removed:
                        self.handle_sensor_changes(added, removed)
                
                # Update previous state
                self.previous_sensor_state = current_sensors.copy()
                
                # Control framerate (display.flip is al gedaan in gui.draw())
                clock.tick(30)  # 30 FPS
                
        except KeyboardInterrupt:
            print("\n\nGame gestopt")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.stockfish:
            self.stockfish.cleanup()
        self.leds.cleanup()
        self.sensors.cleanup()
        self.gui.quit()
        print("Chess Game afgesloten")


def main():
    """Start chess game"""
    from lib.settings import Settings
    settings = Settings()
    brightness_percent = settings.get('brightness', 20)
    brightness_value = int((brightness_percent / 100) * 255)
    brightness_value = max(0, min(255, brightness_value))  # Clamp to valid range
    game = ChessGame(brightness=brightness_value)
    game.run()


if __name__ == '__main__':
    main()
