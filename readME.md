# Jeu d'Échecs — Projet I1 Python

## Lancer le jeu
```bash
python main.py
```

## Lancer les tests
```bash
python -m unittest test_chess -v
```

## Format des coups
`<Pièce><case_origine> <case_destination>`

| Pièce | Lettre |
|-------|--------|
| Roi | K |
| Reine | Q |
| Fou | B |
| Cavalier | N |
| Tour | R |
| Pion | P |

**Exemples :** `Pe2 e4` · `Nb1 c3` · `Bf1 c4`

## Commandes spéciales
- `save` — sauvegarder la partie
- `quit` — quitter
- Tapez `AI` comme nom pour jouer contre l'IA

## Structure
| Fichier | Rôle |
|---------|------|
| `position.py` | Classe Position |
| `pieces.py` | Piece + King, Queen, Bishop, Knight, Rook, Pawn |
| `board.py` | Classe Board (dict + liste) |
| `player.py` | Player + AIPlayer |
| `chess.py` | Classe Chess (boucle de jeu) |
| `main.py` | Point d'entrée |
| `test_chess.py` | 44 tests unitaires |
