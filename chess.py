"""
chess.py
Classe Chess — orchestre la partie d'échecs complète.
"""

import json
import os
from board import Board
from player import Player, AIPlayer
from position import Position
from pieces import King, Queen, Bishop, Knight, Rook, Pawn

PIECE_LETTER_MAP = {"K": King, "Q": Queen, "B": Bishop, "N": Knight, "R": Rook, "P": Pawn}
SAVE_FILE = "chess_save.json"


class Chess:
    """
    Gère globalement la partie d'échecs.
    - board         : Board
    - players       : liste de 2 Player
    - currentPlayer : Player jouant le coup courant
    """

    def __init__(self):
        self.board = Board()
        self.players = []
        self.currentPlayer = None

    def initPlayers(self):
        """Demande les noms. Si 'AI' est saisi, crée un AIPlayer."""
        print("=" * 48)
        print("         ♟  JEU D'ÉCHECS  ♟")
        print("=" * 48)
        self.players = []
        for label, color in [("blanc (commence)", 0), ("noir", 1)]:
            name = input(f"Nom du joueur {label} (tapez 'AI' pour l'IA) : ").strip()
            if not name:
                name = f"Joueur {color + 1}"
            if name.upper() == "AI":
                player = AIPlayer(f"IA-{label}", color)
            else:
                player = Player(name, color)
            self.players.append(player)
            print(f"  ✓ {player} enregistré.")
        self.currentPlayer = self.players[0]

    def displayBoard(self):
        """Affiche le plateau et indique si un roi est en échec."""
        self.board.display()
        for color, label in [(0, "BLANCS"), (1, "NOIRS")]:
            if self.board.is_in_check(color):
                print(f"  ⚠  Le roi {label} est en ÉCHEC !")

    def isValidMove(self, move: str) -> bool:
        """
        Vérifie la légalité du coup saisi.
        Format : <Pièce><orig> <dest>  ex: 'Nb1 c3'
        Vérifie : syntaxe, pièce existante, appartenance, règles, pas d'auto-échec.
        """
        parsed = self._parse_move(move)
        if parsed is None:
            return False
        piece_letter, orig_pos, dest_pos = parsed
        piece = self.board.getPiece(orig_pos)
        if piece is None:
            print(f"  ✗ Aucune pièce en {orig_pos}.")
            return False
        if str(piece).upper() != piece_letter:
            print(f"  ✗ La pièce en {orig_pos} est '{str(piece)}', pas '{piece_letter}'.")
            return False
        if piece.color != self.currentPlayer.color:
            print(f"  ✗ Cette pièce ne vous appartient pas.")
            return False
        if not piece.isValidMove(dest_pos, self.board):
            print(f"  ✗ Déplacement invalide pour {piece_letter} : {orig_pos} → {dest_pos}.")
            return False
        if self._move_leaves_king_in_check(piece, dest_pos):
            print(f"  ✗ Ce coup laisse votre roi en échec !")
            return False
        return True

    def _parse_move(self, move: str):
        move = move.strip()
        parts = move.split()
        if len(parts) != 2:
            print("  ✗ Format invalide. Exemple : 'Nb1 c3' ou 'Pe2 e4'.")
            return None
        src, dst = parts
        if len(src) != 3 or len(dst) != 2:
            print("  ✗ Format invalide. Exemple : 'Nb1 c3'.")
            return None
        piece_letter = src[0].upper()
        if piece_letter not in PIECE_LETTER_MAP:
            print(f"  ✗ Pièce inconnue : '{piece_letter}'. Utilisez K Q B N R P.")
            return None
        try:
            orig_pos = Position.from_string(src[1:])
            dest_pos = Position.from_string(dst)
        except ValueError as e:
            print(f"  ✗ Position invalide : {e}")
            return None
        return piece_letter, orig_pos, dest_pos

    def _move_leaves_king_in_check(self, piece, dest_pos: Position) -> bool:
        """Simule le coup et vérifie si le roi serait en échec après."""
        old_pos = piece.position
        captured = self.board.getPiece(dest_pos)
        self.board.movePiece(piece, dest_pos)
        in_check = self.board.is_in_check(self.currentPlayer.color)
        self.board.movePiece(piece, old_pos)
        if captured is not None:
            self.board._board[str(dest_pos)] = captured
            self.board._pieces.append(captured)
            captured.position = dest_pos
        return in_check

    def updateBoard(self, move: str):
        """Applique le coup sur le plateau."""
        parsed = self._parse_move(move)
        if parsed is None:
            return
        _, orig_pos, dest_pos = parsed
        piece = self.board.getPiece(orig_pos)
        captured = self.board.movePiece(piece, dest_pos)
        if captured:
            print(f"  ★  {str(captured).upper()} {captured.color_name()} capturé(e) !")

    def isCheckMate(self) -> bool:
        """Retourne True si le joueur courant est en échec et mat."""
        color = self.currentPlayer.color
        if not self.board.is_in_check(color):
            return False
        return not self._has_any_legal_move(color)

    def isStalemate(self) -> bool:
        """Retourne True si le joueur courant est en pat."""
        color = self.currentPlayer.color
        if self.board.is_in_check(color):
            return False
        return not self._has_any_legal_move(color)

    def _has_any_legal_move(self, color: int) -> bool:
        """Vérifie s'il existe au moins un coup légal sans laisser le roi en échec."""
        for piece in self.board.get_all_pieces(color):
            for col in Position.COLUMNS:
                for row in range(1, 9):
                    dest = Position(col, row)
                    if dest == piece.position:
                        continue
                    if not piece.isValidMove(dest, self.board):
                        continue
                    old_pos = piece.position
                    captured = self.board.getPiece(dest)
                    self.board.movePiece(piece, dest)
                    still_in_check = self.board.is_in_check(color)
                    self.board.movePiece(piece, old_pos)
                    if captured is not None:
                        self.board._board[str(dest)] = captured
                        self.board._pieces.append(captured)
                        captured.position = dest
                    if not still_in_check:
                        return True
        return False

    def switchPlayer(self):
        """Bascule vers l'autre joueur."""
        self.currentPlayer = self.players[1] if self.currentPlayer == self.players[0] else self.players[0]

    def save(self):
        """Sauvegarde la partie dans un fichier JSON."""
        data = {
            "board": self.board.to_dict(),
            "current_player_color": self.currentPlayer.color,
            "players": [{"name": p.name, "color": p.color, "is_ai": isinstance(p, AIPlayer)}
                        for p in self.players]
        }
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n  💾 Partie sauvegardée dans '{SAVE_FILE}'.")

    def load(self) -> bool:
        """Restaure la partie depuis le fichier de sauvegarde."""
        if not os.path.exists(SAVE_FILE):
            print(f"  ✗ Aucune sauvegarde trouvée.")
            return False
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.board = Board.from_dict(data["board"])
        self.players = []
        for p_data in data["players"]:
            p = AIPlayer(p_data["name"], p_data["color"]) if p_data["is_ai"] else Player(p_data["name"], p_data["color"])
            self.players.append(p)
        self.currentPlayer = next(p for p in self.players if p.color == data["current_player_color"])
        print(f"  ✓ Partie restaurée.")
        return True

    def play(self):
        """
        Boucle principale de jeu.
        Initialisation → affichage → saisie → validation → mise à jour → changement de joueur.
        """
        if os.path.exists(SAVE_FILE):
            choice = input(f"Une sauvegarde existe. Reprendre ? (o/n) : ").strip().lower()
            if choice == "o":
                if not self.load():
                    self.initPlayers()
            else:
                self.initPlayers()
        else:
            self.initPlayers()

        print("\nDébut de la partie ! Bonne chance à tous les deux.")

        while True:
            if isinstance(self.currentPlayer, AIPlayer):
                self.currentPlayer.set_board(self.board)

            self.displayBoard()

            if self.isCheckMate():
                winner = self.players[1 - self.currentPlayer.color]
                print(f"\n  🏆  ÉCHEC ET MAT ! {winner.name} ({winner.color_name()}) gagne !")
                break
            if self.isStalemate():
                print(f"\n  ½  PAT ! Match nul !")
                break

            while True:
                move = self.currentPlayer.askMove()
                if move.lower() == "quit":
                    print("  Partie abandonnée.")
                    return
                if move.lower() == "save":
                    self.save()
                    continue
                if move.lower() == "load":
                    self.load()
                    self.displayBoard()
                    continue
                if self.isValidMove(move):
                    break
                print("  Coup invalide, réessayez.")

            self.updateBoard(move)
            self.switchPlayer()

        replay = input("\nNouvelle partie ? (o/n) : ").strip().lower()
        if replay == "o":
            self.board = Board()
            self.players = []
            self.currentPlayer = None
            self.play()
