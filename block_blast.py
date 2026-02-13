"""Simple Block Blast-style puzzle game using tkinter.

How to play:
- Pick one of the three offered block shapes on the right.
- Click an empty position on the board to place the selected shape.
- Completing a full row or column clears it and grants bonus points.
- Use all three offered shapes to get a fresh set.
- Game ends when no offered shape can be placed anywhere.
"""

from __future__ import annotations

import random
import tkinter as tk
from dataclasses import dataclass


BOARD_SIZE = 8
CELL_SIZE = 44
PALETTE_CELL = 18


@dataclass(frozen=True)
class Piece:
    name: str
    cells: tuple[tuple[int, int], ...]
    color: str


PIECES: tuple[Piece, ...] = (
    Piece("Dot", ((0, 0),), "#ff6b6b"),
    Piece("Line2", ((0, 0), (1, 0)), "#4ecdc4"),
    Piece("Line3", ((0, 0), (1, 0), (2, 0)), "#1a535c"),
    Piece("Line4", ((0, 0), (1, 0), (2, 0), (3, 0)), "#ff9f1c"),
    Piece("Tall2", ((0, 0), (0, 1)), "#7b2cbf"),
    Piece("Tall3", ((0, 0), (0, 1), (0, 2)), "#3a86ff"),
    Piece("Square2", ((0, 0), (1, 0), (0, 1), (1, 1)), "#06d6a0"),
    Piece("L3", ((0, 0), (0, 1), (1, 1)), "#f15bb5"),
    Piece("L4", ((0, 0), (0, 1), (0, 2), (1, 2)), "#9b5de5"),
    Piece("T4", ((0, 0), (1, 0), (2, 0), (1, 1)), "#e76f51"),
    Piece("Z4", ((0, 0), (1, 0), (1, 1), (2, 1)), "#2a9d8f"),
)


class BlockBlastGame:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Block Blast (tkinter)")
        self.root.configure(bg="#1f2430")

        self.board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.selected_piece_index: int | None = None
        self.score = 0
        self.high_score = 0

        outer = tk.Frame(self.root, bg="#1f2430", padx=10, pady=10)
        outer.pack()

        self.board_canvas = tk.Canvas(
            outer,
            width=BOARD_SIZE * CELL_SIZE,
            height=BOARD_SIZE * CELL_SIZE,
            bg="#2f3542",
            highlightthickness=0,
        )
        self.board_canvas.grid(row=0, column=0, rowspan=2)
        self.board_canvas.bind("<Button-1>", self.on_board_click)

        panel = tk.Frame(outer, bg="#1f2430", padx=12)
        panel.grid(row=0, column=1, sticky="n")

        self.score_label = tk.Label(panel, text="Score: 0", fg="#f1f2f6", bg="#1f2430", font=("Arial", 14, "bold"))
        self.score_label.pack(anchor="w", pady=(0, 4))

        self.high_score_label = tk.Label(panel, text="Best: 0", fg="#dfe4ea", bg="#1f2430", font=("Arial", 11))
        self.high_score_label.pack(anchor="w", pady=(0, 10))

        help_text = "Pick a piece → click board\nClear full rows/columns"
        tk.Label(panel, text=help_text, fg="#ced6e0", bg="#1f2430", justify="left").pack(anchor="w", pady=(0, 10))

        self.piece_canvases: list[tk.Canvas] = []
        for idx in range(3):
            c = tk.Canvas(panel, width=6 * PALETTE_CELL, height=6 * PALETTE_CELL, bg="#2f3542", highlightthickness=2)
            c.pack(pady=6)
            c.bind("<Button-1>", lambda _evt, i=idx: self.select_piece(i))
            self.piece_canvases.append(c)

        self.message_label = tk.Label(panel, text="", fg="#ffdd59", bg="#1f2430", font=("Arial", 10, "bold"))
        self.message_label.pack(anchor="w", pady=(12, 8))

        tk.Button(panel, text="New Game", command=self.new_game, bg="#70a1ff", fg="white", relief="flat", padx=10, pady=6).pack(anchor="w")

        self.offered_pieces: list[Piece | None] = []
        self.new_game()

    def new_game(self) -> None:
        self.board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.score = 0
        self.selected_piece_index = None
        self.message_label.config(text="")
        self.refresh_offered_pieces()
        self.redraw_board()
        self.update_score_labels()

    def refresh_offered_pieces(self) -> None:
        self.offered_pieces = [random.choice(PIECES) for _ in range(3)]
        self.selected_piece_index = None
        self.redraw_piece_palette()

    def select_piece(self, index: int) -> None:
        if self.offered_pieces[index] is None:
            return
        self.selected_piece_index = index
        self.redraw_piece_palette()

    def on_board_click(self, event: tk.Event) -> None:
        if self.selected_piece_index is None:
            return

        col = event.x // CELL_SIZE
        row = event.y // CELL_SIZE
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return

        piece = self.offered_pieces[self.selected_piece_index]
        if piece is None:
            return

        if not self.can_place_piece(piece, row, col):
            self.flash_message("Cannot place piece there.")
            return

        self.place_piece(piece, row, col)
        self.offered_pieces[self.selected_piece_index] = None
        self.selected_piece_index = None

        gained = len(piece.cells)
        cleared = self.clear_lines()
        if cleared:
            gained += 8 * cleared
            self.flash_message(f"Cleared {cleared} line(s)! +{8 * cleared}")

        self.score += gained
        self.high_score = max(self.high_score, self.score)
        self.update_score_labels()

        if all(p is None for p in self.offered_pieces):
            self.refresh_offered_pieces()

        self.redraw_piece_palette()
        self.redraw_board()

        if not self.has_any_valid_move():
            self.flash_message("Game over! Press New Game.")

    def can_place_piece(self, piece: Piece, base_row: int, base_col: int) -> bool:
        for dx, dy in piece.cells:
            r = base_row + dy
            c = base_col + dx
            if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
                return False
            if self.board[r][c]:
                return False
        return True

    def place_piece(self, piece: Piece, base_row: int, base_col: int) -> None:
        for dx, dy in piece.cells:
            self.board[base_row + dy][base_col + dx] = piece.color

    def clear_lines(self) -> int:
        full_rows = [r for r in range(BOARD_SIZE) if all(self.board[r][c] for c in range(BOARD_SIZE))]
        full_cols = [c for c in range(BOARD_SIZE) if all(self.board[r][c] for r in range(BOARD_SIZE))]

        for r in full_rows:
            for c in range(BOARD_SIZE):
                self.board[r][c] = 0

        for c in full_cols:
            for r in range(BOARD_SIZE):
                self.board[r][c] = 0

        return len(full_rows) + len(full_cols)

    def has_any_valid_move(self) -> bool:
        active_pieces = [p for p in self.offered_pieces if p is not None]
        if not active_pieces:
            return True

        for piece in active_pieces:
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if self.can_place_piece(piece, row, col):
                        return True
        return False

    def redraw_board(self) -> None:
        self.board_canvas.delete("all")
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                x1, y1 = c * CELL_SIZE, r * CELL_SIZE
                x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
                fill = self.board[r][c] if self.board[r][c] else "#57606f"
                self.board_canvas.create_rectangle(x1 + 1, y1 + 1, x2 - 1, y2 - 1, fill=fill, outline="#2f3542")

    def redraw_piece_palette(self) -> None:
        for idx, canvas in enumerate(self.piece_canvases):
            canvas.delete("all")
            piece = self.offered_pieces[idx]
            if piece is None:
                canvas.configure(highlightbackground="#57606f")
                continue

            is_selected = idx == self.selected_piece_index
            canvas.configure(highlightbackground="#ffd32a" if is_selected else "#57606f")

            min_x = min(x for x, _ in piece.cells)
            min_y = min(y for _, y in piece.cells)
            max_x = max(x for x, _ in piece.cells)
            max_y = max(y for _, y in piece.cells)
            w_cells, h_cells = max_x - min_x + 1, max_y - min_y + 1

            offset_x = (6 - w_cells) * PALETTE_CELL // 2
            offset_y = (6 - h_cells) * PALETTE_CELL // 2

            for x, y in piece.cells:
                px = offset_x + (x - min_x) * PALETTE_CELL
                py = offset_y + (y - min_y) * PALETTE_CELL
                canvas.create_rectangle(px + 1, py + 1, px + PALETTE_CELL - 1, py + PALETTE_CELL - 1, fill=piece.color, outline="#2f3542")

    def update_score_labels(self) -> None:
        self.score_label.config(text=f"Score: {self.score}")
        self.high_score_label.config(text=f"Best: {self.high_score}")

    def flash_message(self, text: str) -> None:
        self.message_label.config(text=text)


def main() -> None:
    root = tk.Tk()
    BlockBlastGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
