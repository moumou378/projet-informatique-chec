"""
player.py
Classes Player (humain) et AIPlayer (intelligence artificielle).
"""

import random
from position import Position


class Player:
    """
    Représente un joueur humain.
    - name  : nom du joueur
    - color : 0 = blanc, 1 = noir
    """

    def __init__(self, name: str, color: int):
        self._name = name
        self._color = color

    @property
    def name(self) -> str:
        return self._name

    @property
    def color(self) -> int:
        return self._color

    def color_name(self) -> str:
        return "Blancs" if self._color == 0 else "Noirs"

    def askMove(self) -> str:
        """Demande au joueur de saisir son coup. Format : <Pièce><orig> <dest>  ex: Nb1 c3"""
        print(f"\n{self._name} ({self.color_name()}) — votre coup")
        print("  Format : <Pièce><orig> <dest>   ex: Nb1 c3  |  Pe2 e4")
        print("  Commandes : 'save' pour sauvegarder, 'quit' pour quitter")
        return input("  > ").strip()

    def __str__(self) -> str:
        return f"{self._name} ({self.color_name()})"


class AIPlayer(Player):
    """
    Joueur IA — génère automatiquement un coup légal aléatoire.
    Hérite de Player et redéfinit askMove().
    """

    def askMove(self) -> str:
        if not hasattr(self, "_board") or self._board is None:
            return ""
        return self._generate_random_move()

    def set_board(self, board):
        """Injecte le plateau courant pour que l'IA puisse l'analyser."""
        self._board = board

    def _generate_random_move(self) -> str:
        """
        Collecte tous les coups légaux, filtre ceux qui laissent le roi en échec,
        et en choisit un au hasard.
        """
        board = self._board
        my_pieces = board.get_all_pieces(self._color)
        random.shuffle(my_pieces)
        legal_moves = []

        for piece in my_pieces:
            for col in Position.COLUMNS:
                for row in range(1, 9):
                    dest = Position(col, row)
                    if dest == piece.position:
                        continue
                    if not piece.isValidMove(dest, board):
                        continue
                    # Simuler pour vérifier que le roi n'est pas en échec après
                    old_pos = piece.position
                    captured = board.getPiece(dest)
                    board.movePiece(piece, dest)
                    in_check = board.is_in_check(self._color)
                    board.movePiece(piece, old_pos)
                    if captured is not None:
                        board._board[str(dest)] = captured
                        board._pieces.append(captured)
                        captured.position = dest
                    if not in_check:
                        legal_moves.append((piece, dest))

        if not legal_moves:
            return ""

        piece, dest = random.choice(legal_moves)
        move_str = f"{str(piece)}{piece.position} {dest}"
        print(f"  [IA] {self._name} joue : {move_str}")
        return move_str
