"""Board implementations for various draughts variants."""
from draughts.boards.base import BaseBoard
from draughts.boards.standard import Board as StandardBoard
from draughts.boards.american import Board as AmericanBoard
from draughts.boards.frisian import Board as FrisianBoard
from draughts.boards.russian import Board as RussianBoard
from draughts.boards.international8 import Board as International8Board

__all__ = ['BaseBoard', 'StandardBoard', 'AmericanBoard', 'FrisianBoard', 'RussianBoard', 'International8Board']

