#!/usr/bin/env python3
"""
Stockfish Chess Engine Wrapper

Python interface naar de Stockfish UCI (Universal Chess Interface) engine.
Gebruikt voor computer tegenstander functionaliteit.

Functionaliteit:
- UCI protocol communicatie via subprocess
- Skill level configuratie (0-20, waarbij 20 = max sterkte ~3200 ELO)
- Best move berekening voor gegeven positie
- Position setup via FEN strings
- Move time control (denktijd in milliseconden)

Engine details:
- Stockfish binary path: /opt/homebrew/bin/stockfish (macOS)
- UCI commands: uci, setoption, position, go, quit
- Skill level 0 = ~800 ELO, skill level 20 = ~3200 ELO

Architectuur:
Deze module is OPZETTELIJK gescheiden van computer_player.py:
- stockfish.py = Pure engine interface (geen GUI dependencies)
- computer_player.py = GUI wrapper (threading + visual feedback)

Voordelen van deze scheiding:
1. Herbruikbaarheid: stockfish.py kan gebruikt worden in CLI, web, etc.
2. Testing: Engine logic kan getest worden zonder GUI
3. Separation of concerns: UCI protocol ≠ visual feedback
4. Toekomstbestendig: Als je ooit een headless versie wilt, gebruik je alleen deze module

Hoofdklasse:
- StockfishEngine: UCI interface met Python API

Wordt gebruikt door: computer_player.py (AI move generation)
"""

import subprocess
import chess


class StockfishEngine:
    """Wrapper voor Stockfish chess engine"""
    
    def __init__(self, stockfish_path=None, skill_level=10, threads=1, depth=15):
        """
        Initialiseer Stockfish engine
        
        Args:
            stockfish_path: Path naar stockfish executable (default: auto-detect)
            skill_level: Sterkte level 0-20 (0=zwakst, 20=sterkst)
            threads: Aantal CPU threads (1-4)
            depth: Maximale zoekdiepte (5-25)
        """
        # Auto-detect stockfish locatie
        if stockfish_path is None:
            # Check standaard locaties
            import os
            if os.path.exists('/usr/games/stockfish'):
                stockfish_path = '/usr/games/stockfish'
            elif os.path.exists('/usr/bin/stockfish'):
                stockfish_path = '/usr/bin/stockfish'
            else:
                stockfish_path = 'stockfish'  # Probeer via PATH
        
        self.stockfish_path = stockfish_path
        self.skill_level = skill_level
        self.threads = threads
        self.depth = depth
        self.process = None
        self.start_engine()
    
    def start_engine(self):
        """Start Stockfish process"""
        try:
            self.process = subprocess.Popen(
                [self.stockfish_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            # Initialiseer UCI mode
            self._send_command("uci")
            self._wait_for("uciok")
            
            # Stel skill level in
            self._send_command(f"setoption name Skill Level value {self.skill_level}")
            
            # Stel threads in
            self._send_command(f"setoption name Threads value {self.threads}")
            
            # Start new game
            self._send_command("ucinewgame")
            self._send_command("isready")
            self._wait_for("readyok")
            
            print(f"Stockfish gestart (skill {self.skill_level}, threads {self.threads}, depth {self.depth})")
        
        except FileNotFoundError:
            print("=" * 60)
            print("ERROR: Stockfish niet gevonden!")
            print("=" * 60)
            print("Installeer stockfish met:")
            print("  sudo apt-get install stockfish")
            print("")
            print("Of run het installatie script:")
            print("  ./install/install_stockfish.sh")
            print("=" * 60)
            self.process = None
        except Exception as e:
            print(f"ERROR bij starten Stockfish: {e}")
            self.process = None
    
    def _send_command(self, command):
        """Stuur command naar Stockfish"""
        if self.process:
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
    
    def _wait_for(self, expected_response):
        """Wacht op specifieke response van Stockfish"""
        if not self.process:
            return
        
        while True:
            line = self.process.stdout.readline().strip()
            if expected_response in line:
                break
    
    def get_best_move(self, board, think_time_ms=None):
        """
        Vraag beste zet op voor huidige positie
        
        Args:
            board: python-chess Board object
            think_time_ms: Denktijd in milliseconden (None = gebruik depth)
        
        Returns:
            chess.Move object of None als engine niet beschikbaar
        """
        if not self.process:
            print("Stockfish engine niet beschikbaar")
            return None
        
        # Stuur positie
        fen = board.fen()
        self._send_command(f"position fen {fen}")
        
        # Vraag beste zet (gebruik think_time of depth)
        # movetime = vaste tijd, wtime/btime = max tijd (Stockfish kan eerder stoppen)
        if think_time_ms is not None:
            # Gebruik wtime/btime voor intelligente tijdverdeling
            # Stockfish stopt eerder als hij zeker is van de beste zet
            self._send_command(f"go wtime {think_time_ms} btime {think_time_ms} winc 0 binc 0")
        else:
            self._send_command(f"go depth {self.depth}")
        
        # Lees output tot we bestmove krijgen
        best_move = None
        while True:
            line = self.process.stdout.readline().strip()
            if line.startswith("bestmove"):
                # Parse: "bestmove e2e4 ponder e7e5"
                parts = line.split()
                if len(parts) >= 2:
                    move_str = parts[1]
                    try:
                        best_move = chess.Move.from_uci(move_str)
                    except:
                        print(f"Ongeldige move van Stockfish: {move_str}")
                break
        
        return best_move
    
    def get_worst_move(self, board):
        """
        Kies de slechtste mogelijk zet op basis van Stockfish evaluatie
        
        Evalueert alle legale zetten en kiest degene die de positie
        het meest verslechtert. Voor wit = laagste evaluatie,
        voor zwart = hoogste evaluatie (omdat scores vanuit wit perspectief zijn).
        
        Args:
            board: python-chess Board object
        
        Returns:
            chess.Move object van de slechtste zet, of None als geen zetten mogelijk
        """
        if not self.process:
            print("Stockfish engine niet beschikbaar")
            return None
        
        legal_moves = list(board.legal_moves)
        
        if not legal_moves:
            return None
        
        if len(legal_moves) == 1:
            # Slechts 1 legale zet, return die
            return legal_moves[0]
        
        print(f"  Evaluating {len(legal_moves)} moves to find worst...")
        move_evaluations = []
        
        # Maak een kopie van het board voor evaluaties
        # Zodat we het originele board niet aanpassen
        eval_board = board.copy()
        
        for move in legal_moves:
            # Maak zet tijdelijk op de KOPIE
            eval_board.push(move)
            
            # Stuur positie naar Stockfish
            fen = eval_board.fen()
            self._send_command(f"position fen {fen}")
            
            # Evalueer met lage depth voor snelheid
            self._send_command("go depth 5")
            
            # Parse evaluatie uit Stockfish output
            score = None
            while True:
                line = self.process.stdout.readline().strip()
                
                # Parse score uit "info" lines
                if line.startswith("info") and "score cp" in line:
                    # Format: "info depth 5 score cp 123 ..."
                    parts = line.split()
                    try:
                        cp_idx = parts.index("cp")
                        score = int(parts[cp_idx + 1])  # Centipawns
                    except (ValueError, IndexError):
                        pass
                
                # Als mate gevonden, gebruik extreme waarde
                elif line.startswith("info") and "score mate" in line:
                    parts = line.split()
                    try:
                        mate_idx = parts.index("mate")
                        mate_in = int(parts[mate_idx + 1])
                        # Mate in X moves = zeer goede/slechte score
                        if mate_in > 0:
                            score = 10000  # Wit wint
                        else:
                            score = -10000  # Zwart wint
                    except (ValueError, IndexError):
                        pass
                
                # Stop bij bestmove
                if line.startswith("bestmove"):
                    break
            
            # Maak zet ongedaan op de kopie
            eval_board.pop()
            
            # Als geen score gevonden, gebruik 0
            if score is None:
                score = 0
            
            move_evaluations.append((move, score))
        
        # Sorteer en kies slechtste zet
        # Voor wit (turn=True): laagste score = slechtst voor wit
        # Voor zwart (turn=False): hoogste score = slechtst voor zwart
        if board.turn:  # Wit aan zet
            worst_move = min(move_evaluations, key=lambda x: x[1])
            print(f"  Worst move for white: {worst_move[0]} (score: {worst_move[1]/100:.2f})")
        else:  # Zwart aan zet
            worst_move = max(move_evaluations, key=lambda x: x[1])
            print(f"  Worst move for black: {worst_move[0]} (score: {worst_move[1]/100:.2f})")
        
        return worst_move[0]
    
    def cleanup(self):
        """Stop Stockfish process"""
        if self.process:
            self._send_command("quit")
            self.process.wait(timeout=2)
            self.process = None
            print("Stockfish gestopt")
