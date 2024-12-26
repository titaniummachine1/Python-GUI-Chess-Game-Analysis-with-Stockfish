import tkinter as tk
import chess.pgn

class MoveHistory:
    def __init__(self, parent, board):
        self.board = board
        self.frame = tk.Frame(parent)
        self.frame.grid(row=0, column=2, rowspan=8, padx=10, pady=5)
        self.history_area = tk.Text(self.frame, width=30, height=20)
        self.history_area.pack(fill=tk.BOTH, expand=True)
        self.history_area.bind("<FocusOut>", self.on_focus_out)

    def update(self, move_stack):
        self.history_area.delete(1.0, tk.END)
        for move in move_stack:
            self.history_area.insert(tk.END, move.uci() + "\n")

    def on_focus_out(self, event):
        pgn_text = self.history_area.get(1.0, tk.END).strip()
        self.load_pgn(pgn_text)

    def load_pgn(self, pgn_text):
        self.board.reset()
        game = chess.pgn.read_game(pgn_text)
        if game:
            self.board = game.board()
            move_stack = list(game.mainline_moves())
            self.update(move_stack)
