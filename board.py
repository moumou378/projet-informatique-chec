from position import Position
from pieces import King, Queen, Bishop, Knight, Rook, Pawn


class Board:

    def __init__(self):
        self._board = {}
        self._pieces = []
        self._init_pieces()

    def _init_pieces(self):
        self._board = {}
        self._pieces = []
        back_row = [("a", Rook), ("b", Knight), ("c", Bishop), ("d", Queen),
                    ("e", King), ("f", Bishop), ("g", Knight), ("h", Rook)]
        for col, PieceClass in back_row:
            self._place(PieceClass(Position(col, 1), 0))
        for col in Position.COLUMNS:
            self._place(Pawn(Position(col, 2), 0))
        for col, PieceClass in back_row:
            self._place(PieceClass(Position(col, 8), 1))
        for col in Position.COLUMNS:
            self._place(Pawn(Position(col, 7), 1))

    def _place(self, piece):
        key = str(piece.position)
        self._board[key] = piece
        self._pieces.append(piece)

    def getPiece(self, position: Position):
        return self._board.get(str(position), None)

    def getPosition(self, piece) -> Position:
        if piece in self._pieces:
            return piece.position
        return None

    def movePiece(self, piece, new_position: Position):
        captured = self.getPiece(new_position)
        if captured is not None:
            del self._board[str(new_position)]
            self._pieces.remove(captured)
        old_key = str(piece.position)
        if old_key in self._board:
            del self._board[old_key]
        piece.position = new_position
        self._board[str(new_position)] = piece
        return captured

    def get_all_pieces(self, color: int = None):
        if color is None:
            return list(self._pieces)
        return [p for p in self._pieces if p.color == color]

    def find_king(self, color: int):
        for piece in self._pieces:
            if isinstance(piece, King) and piece.color == color:
                return piece
        return None

    def is_in_check(self, color: int) -> bool:
        king = self.find_king(color)
        if king is None:
            return False
        for piece in self.get_all_pieces(1 - color):
            if piece.isValidMove(king.position, self):
                return True
        return False

    def display(self):
        print()
        print("    a   b   c   d   e   f   g   h")
        print("  +---+---+---+---+---+---+---+---+")
        for row in range(8, 0, -1):
            line = f"{row} |"
            for col in Position.COLUMNS:
                piece = self.getPiece(Position(col, row))
                if piece is None:
                    cell = " "
                elif piece.color == 0:
                    cell = str(piece).upper()
                else:
                    cell = str(piece).lower()
                line += f" {cell} |"
            print(line + f" {row}")
        print("  +---+---+---+---+---+---+---+---+")
        print("    a   b   c   d   e   f   g   h")
        print()

    def to_dict(self) -> dict:
        return {key: {"type": piece.__class__.__name__, "color": piece.color}
                for key, piece in self._board.items()}

    @staticmethod
    def from_dict(data: dict) -> "Board":
        piece_map = {"King": King, "Queen": Queen, "Bishop": Bishop,
                     "Knight": Knight, "Rook": Rook, "Pawn": Pawn}
        board = Board.__new__(Board)
        board._board = {}
        board._pieces = []
        for pos_str, info in data.items():
            pos = Position.from_string(pos_str)
            piece = piece_map[info["type"]](pos, info["color"])
            board._board[pos_str] = piece
            board._pieces.append(piece)
        return board
