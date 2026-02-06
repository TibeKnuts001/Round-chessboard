#!/usr/bin/env python3
"""
Core Game Components

Shared base classes voor alle board games (chess, checkers, etc.)
"""

from .base_game import BaseGame
from .base_engine import BaseEngine

__all__ = ['BaseGame', 'BaseEngine']
