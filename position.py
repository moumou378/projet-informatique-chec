"""
position.py
Représente une position sur l'échiquier au format standard (ex: "e1", "a8").
"""


class Position:
    """
    Représente une case de l'échiquier.
    - column : caractère entre 'a' et 'h'
    - row    : entier entre 1 et 8
    """

    COLUMNS = "abcdefgh"

    def __init__(self, column: str, row: int):
        if column not in self.COLUMNS:
            raise ValueError(f"Colonne invalide : '{column}'. Doit être entre 'a' et 'h'.")
        if row not in range(1, 9):
            raise ValueError(f"Ligne invalide : {row}. Doit être entre 1 et 8.")
        self._column = column
        self._row = row

    @property
    def column(self) -> str:
        return self._column

    @column.setter
    def column(self, value: str):
        if value not in self.COLUMNS:
            raise ValueError(f"Colonne invalide : '{value}'.")
        self._column = value

    @property
    def row(self) -> int:
        return self._row

    @row.setter
    def row(self, value: int):
        if value not in range(1, 9):
            raise ValueError(f"Ligne invalide : {value}.")
        self._row = value

    def col_index(self) -> int:
        """Retourne l'index numérique de la colonne (0='a', 7='h')."""
        return self.COLUMNS.index(self._column)

    def __str__(self) -> str:
        return f"{self._column}{self._row}"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Position):
            return False
        return self._column == other._column and self._row == other._row

    def __repr__(self) -> str:
        return f"Position('{self._column}', {self._row})"

    @staticmethod
    def from_string(s: str) -> "Position":
        """Crée une Position depuis une chaîne de type 'e1'."""
        if len(s) != 2 or s[0].lower() not in Position.COLUMNS or not s[1].isdigit():
            raise ValueError(f"Format de position invalide : '{s}'. Attendu ex: 'e1'.")
        return Position(s[0].lower(), int(s[1]))
