#!/usr/bin/env python3
"""
Checkers Game Modules

Bevat alle checkers-specifieke code:
- engine.py: CheckersEngine (wrapper rond pydraughts)
- gui.py: CheckersGUI (rendering van checkers bord en stukken)
"""

from .engine import CheckersEngine
from .gui import CheckersGUI

__all__ = ['CheckersEngine', 'CheckersGUI']
