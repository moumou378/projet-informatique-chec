"""
pieces.py
Classe abstraite Piece et ses 6 sous-classes : King, Queen, Bishop, Knight, Rook, Pawn.
Chaque pièce implémente isValidMove() selon les règles officielles des échecs.
"""

from abc import ABC, abstractmethod
from position import Position


class Piece(ABC):
    """
    Classe abstraite — attributs communs à toutes les pièces.
    color : 0 = blanc, 1 = noir
    """

    def __init__(self, position: Position, color: int):
        if color not in (0, 1):
            raise ValueError("La couleur doit être 0 (blanc) ou 1 (noir).")
        self._position = position
        self._color = color

    @property
    def position(self) -> Position:
        return self._position

    @position.setter
    def position(self, value: Position):
        self._position = value

    @property
    def color(self) -> int:
        return self._color

    def color_name(self) -> str:
        return "blanc" if self._color == 0 else "noir"

    @abstractmethod
    def isValidMove(self, new_position: Position, board) -> bool:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    def _path_is_clear(self, new_position: Position, board) -> bool:
        """
        Vérifie que toutes les cases intermédiaires entre la position actuelle
        et new_position sont vides (pour les pièces qui glissent : Tour, Fou, Reine).
        Ne vérifie PAS la case de destination elle-même.
        """
        c0 = self._position.col_index()
        r0 = self._position.row
        c1 = new_position.col_index()
        r1 = new_position.row

        dc = 0 if c1 == c0 else (1 if c1 > c0 else -1)
        dr = 0 if r1 == r0 else (1 if r1 > r0 else -1)

        cur_c = c0 + dc
        cur_r = r0 + dr
        cols = Position.COLUMNS

        while (cur_c, cur_r) != (c1, r1):
            if board.getPiece(Position(cols[cur_c], cur_r)) is not None:
                return False
            cur_c += dc
            cur_r += dr
        return True


class King(Piece):
    """
    Déplacement : 1 case dans n'importe quelle direction (8 cases possibles).
    Ne peut pas se déplacer sur une case occupée par une pièce amie.
    """
    def __str__(self) -> str:
        return "K"

    def isValidMove(self, new_position: Position, board) -> bool:
        dc = abs(new_position.col_index() - self._position.col_index())
        dr = abs(new_position.row - self._position.row)
        if not (max(dc, dr) == 1):
            return False
        target = board.getPiece(new_position)
        if target is not None and target.color == self._color:
            return False
        return True


class Queen(Piece):
    """
    Déplacement : ligne droite (horizontal/vertical) OU diagonale,
    nombre quelconque de cases, sans obstacle sur le chemin.
    """
    def __str__(self) -> str:
        return "Q"

    def isValidMove(self, new_position: Position, board) -> bool:
        dc = abs(new_position.col_index() - self._position.col_index())
        dr = abs(new_position.row - self._position.row)
        is_straight = (dc == 0 and dr > 0) or (dr == 0 and dc > 0)
        is_diagonal = (dc == dr and dc > 0)
        if not (is_straight or is_diagonal):
            return False
        if not self._path_is_clear(new_position, board):
            return False
        target = board.getPiece(new_position)
        if target is not None and target.color == self._color:
            return False
        return True


class Bishop(Piece):
    """
    Déplacement : uniquement en diagonale, nombre quelconque de cases.
    Le chemin doit être libre.
    """
    def __str__(self) -> str:
        return "B"

    def isValidMove(self, new_position: Position, board) -> bool:
        dc = abs(new_position.col_index() - self._position.col_index())
        dr = abs(new_position.row - self._position.row)
        if dc != dr or dc == 0:
            return False
        if not self._path_is_clear(new_position, board):
            return False
        target = board.getPiece(new_position)
        if target is not None and target.color == self._color:
            return False
        return True


class Knight(Piece):
    """
    Déplacement : en L — 2 cases dans une direction puis 1 case perpendiculaire.
    Peut sauter par-dessus les autres pièces.
    """
    def __str__(self) -> str:
        return "N"

    def isValidMove(self, new_position: Position, board) -> bool:
        dc = abs(new_position.col_index() - self._position.col_index())
        dr = abs(new_position.row - self._position.row)
        if not ((dc == 2 and dr == 1) or (dc == 1 and dr == 2)):
            return False
        target = board.getPiece(new_position)
        if target is not None and target.color == self._color:
            return False
        return True


class Rook(Piece):
    """
    Déplacement : horizontal ou vertical, nombre quelconque de cases.
    Le chemin doit être libre.
    """
    def __str__(self) -> str:
        return "R"

    def isValidMove(self, new_position: Position, board) -> bool:
        dc = abs(new_position.col_index() - self._position.col_index())
        dr = abs(new_position.row - self._position.row)
        if not ((dc == 0 and dr > 0) or (dr == 0 and dc > 0)):
            return False
        if not self._path_is_clear(new_position, board):
            return False
        target = board.getPiece(new_position)
        if target is not None and target.color == self._color:
            return False
        return True


class Pawn(Piece):
    """
    Règles de déplacement du Pion :
    1. AVANCÉE SIMPLE  : 1 case vers l'avant si la case est vide.
       Blanc (color=0) monte (row+1), Noir (color=1) descend (row-1).
    2. AVANCÉE DOUBLE  : 2 cases depuis la rangée de départ (rang 2 ou 7),
       les deux cases devant doivent être vides.
    3. CAPTURE DIAGONALE : 1 case en diagonale avant si une pièce adverse s'y trouve.
    """
    def __str__(self) -> str:
        return "P"

    def _direction(self) -> int:
        return 1 if self._color == 0 else -1

    def _start_row(self) -> int:
        return 2 if self._color == 0 else 7

    def isValidMove(self, new_position: Position, board) -> bool:
        direction = self._direction()
        start_row = self._start_row()
        dc = new_position.col_index() - self._position.col_index()
        dr = new_position.row - self._position.row
        target = board.getPiece(new_position)

        # Cas 1 : avancée simple
        if dc == 0 and dr == direction:
            return target is None

        # Cas 2 : avancée double depuis la rangée de départ
        if dc == 0 and dr == 2 * direction and self._position.row == start_row:
            intermediate = Position(self._position.column, self._position.row + direction)
            return (target is None) and (board.getPiece(intermediate) is None)

        # Cas 3 : capture en diagonale
        if abs(dc) == 1 and dr == direction:
            return target is not None and target.color != self._color

        return False
