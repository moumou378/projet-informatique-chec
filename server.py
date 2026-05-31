"""
server.py
Serveur Flask — fait le pont entre la logique Python du jeu d'échecs
et l'interface 3D Three.js dans le navigateur.

Lancement : python server.py
Puis ouvrir : http://localhost:5000
"""

import sys
import os
import json

# Ajouter le dossier parent pour importer les fichiers du jeu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request, render_template, session
from flask import send_from_directory

# Import de la logique du jeu
from position import Position
from board import Board
from pieces import King, Queen, Bishop, Knight, Rook, Pawn
from player import Player, AIPlayer
from chess_game import Chess

app = Flask(__name__)
app.secret_key = "chess3d_secret_key_2025"

# ── État global de la partie ──────────────────────────────────────────────────
game_state = {
    "board": None,
    "current_color": 0,       # 0 = blanc, 1 = noir
    "status": "waiting",      # waiting | playing | check | checkmate | stalemate
    "players": ["Joueur 1", "Joueur 2"],
    "ai_enabled": False,
    "selected": None,
    "legal_moves": [],
    "captured_white": [],
    "captured_black": [],
    "move_history": [],
    "last_move": None,
}

def init_game(player1="Joueur 1", player2="Joueur 2", ai=False):
    """Initialise ou réinitialise une partie."""
    game_state["board"] = Board()
    game_state["current_color"] = 0
    game_state["status"] = "playing"
    game_state["players"] = [player1, player2]
    game_state["ai_enabled"] = ai
    game_state["selected"] = None
    game_state["legal_moves"] = []
    game_state["captured_white"] = []
    game_state["captured_black"] = []
    game_state["move_history"] = []
    game_state["last_move"] = None


def board_to_json(board: Board) -> list:
    """Convertit le plateau en liste JSON pour Three.js."""
    pieces = []
    for col in Position.COLUMNS:
        for row in range(1, 9):
            pos = Position(col, row)
            piece = board.getPiece(pos)
            if piece:
                pieces.append({
                    "type": piece.__class__.__name__,
                    "color": piece.color,
                    "col": pos.col_index(),   # 0-7
                    "row": row - 1,            # 0-7
                    "pos": str(pos),
                })
    return pieces


def get_legal_moves_for(col_idx: int, row_idx: int) -> list:
    """Retourne les coups légaux pour la pièce en (col_idx, row_idx)."""
    board = game_state["board"]
    if board is None:
        return []
    pos = Position(Position.COLUMNS[col_idx], row_idx + 1)
    piece = board.getPiece(pos)
    if piece is None or piece.color != game_state["current_color"]:
        return []

    legal = []
    for c in Position.COLUMNS:
        for r in range(1, 9):
            dest = Position(c, r)
            if dest == pos:
                continue
            if not piece.isValidMove(dest, board):
                continue
            # Simuler pour vérifier pas d'auto-échec
            old_pos = piece.position
            captured = board.getPiece(dest)
            board.movePiece(piece, dest)
            in_check = board.is_in_check(piece.color)
            board.movePiece(piece, old_pos)
            if captured is not None:
                board._board[str(dest)] = captured
                board._pieces.append(captured)
                captured.position = dest
            if not in_check:
                legal.append({"col": dest.col_index(), "row": dest.row - 1})
    return legal


def has_any_legal_move(color: int) -> bool:
    board = game_state["board"]
    for piece in board.get_all_pieces(color):
        for c in Position.COLUMNS:
            for r in range(1, 9):
                dest = Position(c, r)
                if dest == piece.position:
                    continue
                if not piece.isValidMove(dest, board):
                    continue
                old_pos = piece.position
                captured = board.getPiece(dest)
                board.movePiece(piece, dest)
                still_check = board.is_in_check(color)
                board.movePiece(piece, old_pos)
                if captured is not None:
                    board._board[str(dest)] = captured
                    board._pieces.append(captured)
                    captured.position = dest
                if not still_check:
                    return True
    return False


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/start", methods=["POST"])
def start_game():
    data = request.json or {}
    p1 = data.get("player1", "Joueur 1")
    p2 = data.get("player2", "Joueur 2")
    ai = data.get("ai", False)
    init_game(p1, p2, ai)
    return jsonify({"ok": True, "board": board_to_json(game_state["board"])})


@app.route("/api/state", methods=["GET"])
def get_state():
    board = game_state["board"]
    if board is None:
        return jsonify({"status": "waiting"})
    in_check = board.is_in_check(game_state["current_color"])
    return jsonify({
        "board": board_to_json(board),
        "current_color": game_state["current_color"],
        "status": game_state["status"],
        "players": game_state["players"],
        "in_check": in_check,
        "last_move": game_state["last_move"],
        "captured_white": game_state["captured_white"],
        "captured_black": game_state["captured_black"],
        "move_history": game_state["move_history"][-10:],
    })


@app.route("/api/select", methods=["POST"])
def select_piece():
    """Sélectionne une pièce et retourne ses coups légaux."""
    data = request.json
    col = data.get("col")
    row = data.get("row")
    legal = get_legal_moves_for(col, row)
    game_state["selected"] = {"col": col, "row": row}
    game_state["legal_moves"] = legal
    return jsonify({"legal_moves": legal})


@app.route("/api/move", methods=["POST"])
def make_move():
    """Effectue un coup : from_col/from_row -> to_col/to_row."""
    data = request.json
    board = game_state["board"]
    if board is None:
        return jsonify({"ok": False, "error": "Partie non démarrée"})

    fc = data["from_col"]
    fr = data["from_row"]
    tc = data["to_col"]
    tr = data["to_row"]

    from_pos = Position(Position.COLUMNS[fc], fr + 1)
    to_pos   = Position(Position.COLUMNS[tc], tr + 1)

    piece = board.getPiece(from_pos)
    if piece is None:
        return jsonify({"ok": False, "error": "Aucune pièce ici"})
    if piece.color != game_state["current_color"]:
        return jsonify({"ok": False, "error": "Ce n'est pas votre pièce"})
    if not piece.isValidMove(to_pos, board):
        return jsonify({"ok": False, "error": "Coup invalide"})

    # Vérif auto-échec
    old_pos = piece.position
    captured_sim = board.getPiece(to_pos)
    board.movePiece(piece, to_pos)
    if board.is_in_check(piece.color):
        board.movePiece(piece, old_pos)
        if captured_sim:
            board._board[str(to_pos)] = captured_sim
            board._pieces.append(captured_sim)
            captured_sim.position = to_pos
        return jsonify({"ok": False, "error": "Ce coup laisse votre roi en échec !"})
    # Coup valide — annuler la sim et rejouer proprement
    board.movePiece(piece, old_pos)
    if captured_sim:
        board._board[str(to_pos)] = captured_sim
        board._pieces.append(captured_sim)
        captured_sim.position = to_pos

    # Appliquer le coup
    captured = board.movePiece(piece, to_pos)
    game_state["last_move"] = {"from": [fc, fr], "to": [tc, tr]}

    # Enregistrer capture
    if captured:
        name = captured.__class__.__name__
        if captured.color == 0:
            game_state["captured_white"].append(name)
        else:
            game_state["captured_black"].append(name)

    # Historique
    cols = "abcdefgh"
    game_state["move_history"].append(
        f"{piece.__class__.__name__[0]}{cols[fc]}{fr+1}→{cols[tc]}{tr+1}"
    )

    # Changer de joueur
    next_color = 1 - game_state["current_color"]
    game_state["current_color"] = next_color

    # Vérifier fin de partie
    in_check = board.is_in_check(next_color)
    has_moves = has_any_legal_move(next_color)

    if not has_moves:
        if in_check:
            game_state["status"] = "checkmate"
            winner = game_state["players"][1 - next_color]
            return jsonify({
                "ok": True,
                "board": board_to_json(board),
                "status": "checkmate",
                "winner": winner,
                "captured": captured.__class__.__name__ if captured else None,
            })
        else:
            game_state["status"] = "stalemate"
            return jsonify({
                "ok": True,
                "board": board_to_json(board),
                "status": "stalemate",
                "captured": captured.__class__.__name__ if captured else None,
            })

    game_state["status"] = "check" if in_check else "playing"

    # IA si activée
    ai_move = None
    if game_state["ai_enabled"] and next_color == 1:
        import random
        ai_piece_list = board.get_all_pieces(1)
        random.shuffle(ai_piece_list)
        ai_legal = []
        for ap in ai_piece_list:
            for ac in Position.COLUMNS:
                for ar in range(1, 9):
                    adest = Position(ac, ar)
                    if adest == ap.position:
                        continue
                    if not ap.isValidMove(adest, board):
                        continue
                    old = ap.position
                    cap2 = board.getPiece(adest)
                    board.movePiece(ap, adest)
                    chk = board.is_in_check(1)
                    board.movePiece(ap, old)
                    if cap2:
                        board._board[str(adest)] = cap2
                        board._pieces.append(cap2)
                        cap2.position = adest
                    if not chk:
                        ai_legal.append((ap, adest))
        if ai_legal:
            # Préférer les captures
            captures = [(p, d) for p, d in ai_legal if board.getPiece(d)]
            choice = random.choice(captures if captures else ai_legal)
            ap, adest = choice
            afc = ap.position.col_index()
            afr = ap.position.row - 1
            atc = adest.col_index()
            atr = adest.row - 1
            ai_cap = board.movePiece(ap, adest)
            if ai_cap:
                if ai_cap.color == 0:
                    game_state["captured_white"].append(ai_cap.__class__.__name__)
                else:
                    game_state["captured_black"].append(ai_cap.__class__.__name__)
            game_state["last_move"] = {"from": [afc, afr], "to": [atc, atr]}
            game_state["move_history"].append(
                f"IA:{ap.__class__.__name__[0]}{cols[afc]}{afr+1}→{cols[atc]}{atr+1}"
            )
            game_state["current_color"] = 0
            ai_move = {"from": [afc, afr], "to": [atc, atr]}

            in_check2 = board.is_in_check(0)
            has_moves2 = has_any_legal_move(0)
            if not has_moves2:
                game_state["status"] = "checkmate" if in_check2 else "stalemate"
            else:
                game_state["status"] = "check" if in_check2 else "playing"

    return jsonify({
        "ok": True,
        "board": board_to_json(board),
        "status": game_state["status"],
        "current_color": game_state["current_color"],
        "captured": captured.__class__.__name__ if captured else None,
        "in_check": board.is_in_check(game_state["current_color"]),
        "ai_move": ai_move,
    })


@app.route("/api/save", methods=["POST"])
def save():
    board = game_state["board"]
    if board is None:
        return jsonify({"ok": False})
    data = {
        "board": board.to_dict(),
        "current_color": game_state["current_color"],
        "players": game_state["players"],
        "ai_enabled": game_state["ai_enabled"],
        "move_history": game_state["move_history"],
        "captured_white": game_state["captured_white"],
        "captured_black": game_state["captured_black"],
    }
    with open("chess_save.json", "w") as f:
        json.dump(data, f, indent=2)
    return jsonify({"ok": True})


@app.route("/api/load", methods=["POST"])
def load():
    try:
        with open("chess_save.json") as f:
            data = json.load(f)
        game_state["board"] = Board.from_dict(data["board"])
        game_state["current_color"] = data["current_color"]
        game_state["players"] = data["players"]
        game_state["ai_enabled"] = data.get("ai_enabled", False)
        game_state["move_history"] = data.get("move_history", [])
        game_state["captured_white"] = data.get("captured_white", [])
        game_state["captured_black"] = data.get("captured_black", [])
        game_state["status"] = "playing"
        game_state["last_move"] = None
        return jsonify({"ok": True, "board": board_to_json(game_state["board"])})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


if __name__ == "__main__":
    print("=" * 50)
    print("  ♟  Jeu d'Échecs 3D — Serveur Flask")
    print("  Ouvre http://localhost:5000 dans ton navigateur")
    print("=" * 50)
    app.run(debug=True, port=5000)
