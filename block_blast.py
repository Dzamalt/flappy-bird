"""Simple Block Blast-style puzzle game using tkinter.

How to play:
- Drag one of the three offered block shapes onto the board.
- You can also click a piece and click the board to place it.
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
        self.dragging_piece_index: int | None = None
        self.dragging_piece: Piece | None = None
        self.score = 0
        self.high_score = 0
        self.clear_effect_job: str | None = None
        self.clear_effect_frame = 0
        self.clear_effect_rows: list[int] = []
        self.clear_effect_cols: list[int] = []

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

        help_text = "Drag piece → drop on board\nOr click piece then board"
        tk.Label(panel, text=help_text, fg="#ced6e0", bg="#1f2430", justify="left").pack(anchor="w", pady=(0, 10))

        self.piece_canvases: list[tk.Canvas] = []
        for idx in range(3):
            c = tk.Canvas(panel, width=6 * PALETTE_CELL, height=6 * PALETTE_CELL, bg="#2f3542", highlightthickness=2)
            c.pack(pady=6)
            c.bind("<Button-1>", lambda _evt, i=idx: self.select_piece(i))
            c.bind("<ButtonPress-1>", lambda _evt, i=idx: self.start_drag(i))
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
        self.stop_drag()
        self.message_label.config(text="")
        self.refresh_offered_pieces()
        self.redraw_board()
        self.update_score_labels()
        self.play_sound("new_game")

    def refresh_offered_pieces(self) -> None:
        self.offered_pieces = [random.choice(PIECES) for _ in range(3)]
        self.selected_piece_index = None
        self.redraw_piece_palette()

    def select_piece(self, index: int) -> None:
        if self.offered_pieces[index] is None:
            return
        self.selected_piece_index = index
        self.redraw_piece_palette()

    def start_drag(self, index: int) -> None:
        piece = self.offered_pieces[index]
        if piece is None:
            return
        self.dragging_piece_index = index
        self.dragging_piece = piece
        self.selected_piece_index = index
        self.play_sound("pick")
        self.root.bind_all("<Motion>", self.on_global_motion)
        self.root.bind_all("<ButtonRelease-1>", self.on_global_release)
        self.redraw_piece_palette()
        self.update_drag_preview(*self.root.winfo_pointerxy())

    def stop_drag(self) -> None:
        self.dragging_piece_index = None
        self.dragging_piece = None
        self.board_canvas.delete("drag_preview")
        self.root.unbind_all("<Motion>")
        self.root.unbind_all("<ButtonRelease-1>")

    def on_global_motion(self, _event: tk.Event) -> None:
        if self.dragging_piece is None:
            return
        self.update_drag_preview(*self.root.winfo_pointerxy())

    def on_global_release(self, _event: tk.Event) -> None:
        if self.dragging_piece is None or self.dragging_piece_index is None:
            return

        row, col = self.pointer_to_board_cell(*self.root.winfo_pointerxy())
        if row is not None and col is not None and self.can_place_piece(self.dragging_piece, row, col):
            self.place_selected_piece(self.dragging_piece_index, row, col)
        else:
            self.play_sound("invalid")

        self.stop_drag()
        self.redraw_piece_palette()
        self.redraw_board()

    def pointer_to_board_cell(self, pointer_x: int, pointer_y: int) -> tuple[int | None, int | None]:
        board_x = pointer_x - self.board_canvas.winfo_rootx()
        board_y = pointer_y - self.board_canvas.winfo_rooty()
        col = board_x // CELL_SIZE
        row = board_y // CELL_SIZE
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return None, None
        return row, col

    def update_drag_preview(self, pointer_x: int, pointer_y: int) -> None:
        if self.dragging_piece is None:
            return

        self.board_canvas.delete("drag_preview")
        row, col = self.pointer_to_board_cell(pointer_x, pointer_y)
        if row is None or col is None:
            return

        valid = self.can_place_piece(self.dragging_piece, row, col)
        border = "#7bed9f" if valid else "#ff6b81"
        fill = "#7bed9f" if valid else "#ff4757"

        for dx, dy in self.dragging_piece.cells:
            r = row + dy
            c = col + dx
            if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
                continue
            x1, y1 = c * CELL_SIZE, r * CELL_SIZE
            x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
            self.board_canvas.create_rectangle(
                x1 + 2,
                y1 + 2,
                x2 - 2,
                y2 - 2,
                fill=fill,
                outline=border,
                width=2,
                stipple="gray50",
                tags="drag_preview",
            )

    def on_board_click(self, event: tk.Event) -> None:
        if self.selected_piece_index is None:
            return
        row = event.y // CELL_SIZE
        col = event.x // CELL_SIZE
        self.place_selected_piece(self.selected_piece_index, row, col)

    def place_selected_piece(self, piece_index: int, row: int, col: int) -> bool:
        piece = self.offered_pieces[piece_index]
        if piece is None:
            return False

        if not self.can_place_piece(piece, row, col):
            self.flash_message("Cannot place piece there.")
            self.play_sound("invalid")
            return False

        self.place_piece(piece, row, col)
        self.offered_pieces[piece_index] = None
        self.selected_piece_index = None

        gained = len(piece.cells)
        cleared_rows, cleared_cols = self.clear_lines()
        cleared = len(cleared_rows) + len(cleared_cols)
        if cleared:
            gained += 8 * cleared
            self.flash_message(f"Cleared {cleared} line(s)! +{8 * cleared}")
            self.start_clear_effect(cleared_rows, cleared_cols)

        self.score += gained
        self.high_score = max(self.high_score, self.score)
        self.update_score_labels()

        if all(p is None for p in self.offered_pieces):
            self.refresh_offered_pieces()

        self.redraw_piece_palette()
        self.redraw_board()

        if not self.has_any_valid_move():
            self.flash_message("Game over! Press New Game.")
            self.play_sound("game_over")

        return True

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

    def clear_lines(self) -> tuple[list[int], list[int]]:
        full_rows = [r for r in range(BOARD_SIZE) if all(self.board[r][c] for c in range(BOARD_SIZE))]
        full_cols = [c for c in range(BOARD_SIZE) if all(self.board[r][c] for r in range(BOARD_SIZE))]

        for r in full_rows:
            for c in range(BOARD_SIZE):
                self.board[r][c] = 0

        for c in full_cols:
            for r in range(BOARD_SIZE):
                self.board[r][c] = 0

        return full_rows, full_cols

    def start_clear_effect(self, rows: list[int], cols: list[int]) -> None:
        self.clear_effect_rows = rows
        self.clear_effect_cols = cols
        self.clear_effect_frame = 0
        if self.clear_effect_job is not None:
            self.root.after_cancel(self.clear_effect_job)
        self.animate_clear_effect()

    def animate_clear_effect(self) -> None:
        self.redraw_board()
        flash_colors = ("#fff08a", "#ffd32a", "#7bed9f")
        color = flash_colors[self.clear_effect_frame % len(flash_colors)]

        for row in self.clear_effect_rows:
            y1 = row * CELL_SIZE + 4
            y2 = (row + 1) * CELL_SIZE - 4
            self.board_canvas.create_rectangle(0, y1, BOARD_SIZE * CELL_SIZE, y2, fill=color, outline="", stipple="gray50")

        for col in self.clear_effect_cols:
            x1 = col * CELL_SIZE + 4
            x2 = (col + 1) * CELL_SIZE - 4
            self.board_canvas.create_rectangle(x1, 0, x2, BOARD_SIZE * CELL_SIZE, fill=color, outline="", stipple="gray50")

        spark_radius = 4 + self.clear_effect_frame * 2
        for row in self.clear_effect_rows:
            for col in range(BOARD_SIZE):
                cx = col * CELL_SIZE + CELL_SIZE // 2
                cy = row * CELL_SIZE + CELL_SIZE // 2
                self.board_canvas.create_oval(
                    cx - spark_radius,
                    cy - spark_radius,
                    cx + spark_radius,
                    cy + spark_radius,
                    outline="#fefefe",
                    width=2,
                )

        for col in self.clear_effect_cols:
            for row in range(BOARD_SIZE):
                cx = col * CELL_SIZE + CELL_SIZE // 2
                cy = row * CELL_SIZE + CELL_SIZE // 2
                self.board_canvas.create_oval(
                    cx - spark_radius,
                    cy - spark_radius,
                    cx + spark_radius,
                    cy + spark_radius,
                    outline="#fefefe",
                    width=2,
                )

        self.clear_effect_frame += 1
        if self.clear_effect_frame < 6:
            self.clear_effect_job = self.root.after(65, self.animate_clear_effect)
        else:
            self.clear_effect_job = None
            self.redraw_board()

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

    def play_sound(self, kind: str) -> None:
        patterns = {
            "new_game": (0, 100),
            "pick": (0,),
            "place": (0,),
            "clear": (0, 70),
            "invalid": (0, 80, 160),
            "game_over": (0, 120, 240),
        }
        for delay in patterns.get(kind, (0,)):
            self.root.after(delay, self.root.bell)


def main() -> None:
    root = tk.Tk()
    BlockBlastGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
