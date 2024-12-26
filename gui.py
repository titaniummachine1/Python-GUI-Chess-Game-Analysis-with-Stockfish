import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import chess
import chess.pgn
from PIL import Image, ImageTk
from engine import ChessEngine
from move_history import MoveHistory
from navigation import Navigation
import math
from move_gen import MoveGen


class ChessAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess Analyzer with Stockfish")

        self.engine = ChessEngine("stockfish/stockfish-windows-x86-64-avx2.exe")
        self.board = chess.Board()
        self.selected_square = None
        self.piece_images = self.load_piece_images()
        self.move_stack = []
        self.cumulative_score = 0  # Initialize cumulative score
        self.move_gen = MoveGen(self.board)
        self.board_flipped = False  # Track if the board is flipped
        self.setup_gui()
        self.update_analysis_bar()  # Initialize the evaluation bar

    def setup_gui(self):
        self.frame = tk.Frame(self.root)
        self.frame.pack(padx=10, pady=10)

        self.analysis_bar = tk.Canvas(self.frame, width=20, height=400, bg="#FFFFFF")
        self.analysis_bar.grid(row=0, column=0, rowspan=8, padx=5)

        self.white_drawback_var = tk.StringVar(value="None")
        self.white_drawback_menu = tk.OptionMenu(
            self.frame, self.white_drawback_var, "None", "no_diagonal_capture", "king_must_capture", "no_pawn_moves", command=lambda _: self.set_drawback(chess.WHITE)
        )
        self.white_drawback_menu.grid(row=9, column=1, columnspan=2, pady=5)

        self.board_canvas = tk.Canvas(self.frame, width=400, height=400)
        self.board_canvas.grid(row=1, column=1, rowspan=8, padx=5)

        self.black_drawback_var = tk.StringVar(value="None")
        self.black_drawback_menu = tk.OptionMenu(
            self.frame, self.black_drawback_var, "None", "no_diagonal_capture", "king_must_capture", "no_pawn_moves", command=lambda _: self.set_drawback(chess.BLACK)
        )
        self.black_drawback_menu.grid(row=0, column=1, columnspan=2, pady=5)

        self.analysis_area = scrolledtext.ScrolledText(self.frame, width=50, height=20)
        self.analysis_area.grid(row=1, column=2, rowspan=8, padx=10, pady=5)

        self.load_pgn_button = tk.Button(
            self.frame, text="Load PGN", command=self.load_pgn
        )
        self.load_pgn_button.grid(row=10, column=1, columnspan=2, pady=5)

        self.reset_board_button = tk.Button(
            self.frame, text="Reset Board", command=self.reset_board
        )
        self.reset_board_button.grid(row=10, column=3, columnspan=2, pady=5)

        self.flip_board_button = tk.Button(
            self.frame, text="Flip Board", command=self.flip_board
        )
        self.flip_board_button.grid(row=10, column=5, columnspan=2, pady=5)

        self.board_canvas.bind("<Button-1>", self.on_board_click)

        self.navigation = Navigation(self.frame, self.next_move, self.prev_move)
        self.navigation.frame.grid(row=11, column=1, columnspan=4, pady=5)

        self.move_history = MoveHistory(self.frame)
        self.move_history.frame.grid(row=1, column=3, rowspan=8, padx=5, pady=5)

        self.refresh_board()

    def set_drawback(self, color):
        """
        Set the drawback for the specified player.
        """
        if color == chess.WHITE:
            drawback = self.white_drawback_var.get()
        else:
            drawback = self.black_drawback_var.get()

        if drawback == "None":
            drawback = None
        self.move_gen.set_drawback(color, drawback)
        self.refresh_board()

    def load_pgn(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")]
        )
        if not file_path:
            return

        with open(file_path) as f:
            game = chess.pgn.read_game(f)
            if game:
                self.board = game.board()
                self.move_stack = list(game.mainline_moves())
            else:
                messagebox.showerror("Error", "Failed to load PGN file.")
                return

        self.analysis_area.delete(1.0, tk.END)
        self.refresh_board()
        self.analyze_current_position()
        self.move_history.update(self.move_stack)
        self.update_analysis_bar()

    def reset_board(self):
        self.board.reset()
        self.move_stack = []
        self.analysis_area.delete(1.0, tk.END)
        self.cumulative_score = 0  # Reset cumulative score
        self.refresh_board()
        self.move_history.update(self.move_stack)
        self.update_analysis_bar()

    def flip_board(self):
        """
        Flip the board orientation.
        """
        self.board_flipped = not self.board_flipped
        self.update_drawback_menus()
        self.refresh_board()

    def update_drawback_menus(self):
        """
        Update the position of the drawback menus based on the board orientation.
        """
        if self.board_flipped:
            self.white_drawback_menu.grid(row=0, column=1, columnspan=2, pady=5)
            self.black_drawback_menu.grid(row=9, column=1, columnspan=2, pady=5)
        else:
            self.white_drawback_menu.grid(row=9, column=1, columnspan=2, pady=5)
            self.black_drawback_menu.grid(row=0, column=1, columnspan=2, pady=5)

    def on_board_click(self, event):
        x, y = event.x, event.y
        if self.board_flipped:
            x, y = 400 - x, 400 - y
        col = x // 50
        row = 7 - (y // 50)
        square = chess.square(col, row)
        move = chess.Move(self.selected_square, square)
    
        if self.selected_square is None:
            if self.board.piece_at(square):
                self.selected_square = square
                self.highlight_legal_moves(square)
        else:
            if self.move_gen.is_custom_legal_move(move):
                self.board.push(move)
                self.selected_square = None  # Deselect after a valid move
                self.analyze_current_position()  # Update analysis
                self.move_history.update(self.board.move_stack)  # Update move history
                self.update_analysis_bar()  # Update analysis bar
                if self.move_gen.is_game_over():
                    self.handle_game_over()
            else:
                if self.board.piece_at(square):
                    self.selected_square = square
                    self.highlight_legal_moves(square)
                else:
                    self.selected_square = None
    
        self.refresh_board()  # Refresh to show updates

    def highlight_legal_moves(self, square):
        self.board_canvas.delete("highlight")
        legal_moves = self.move_gen.get_custom_legal_moves()
        for move in legal_moves:
            if move.from_square == square:
                col, row = chess.square_file(move.to_square), chess.square_rank(move.to_square)
                if self.board_flipped:
                    col, row = 7 - col, 7 - row
                x1, y1 = col * 50 + 20, (7 - row) * 50 + 20
                x2, y2 = x1 + 10, y1 + 10
                self.board_canvas.create_oval(x1, y1, x2, y2, fill="black", outline="", stipple="gray50", tags="highlight")

    def handle_game_over(self):
        winner = "White" if self.board.turn == chess.BLACK else "Black"
        messagebox.showinfo("Game Over", f"{winner} wins!")
        self.reset_board()

    def analyze_current_position(self):
        analysis = self.engine.analyze(self.board)
        self.analysis_area.delete(1.0, tk.END)
        if self.board.move_stack:
            self.analysis_area.insert(tk.END, f"Move: {self.board.peek()}\n")
        
        score = analysis['score']
        if self.board.turn == chess.BLACK:
            score = -score  # Invert score if it's black's turn
    
        scaled_score = score / 100  # Scale the score to pawns
        self.analysis_area.insert(tk.END, f"Score: {scaled_score:.2f}\n")
        if "pv" in analysis:
            self.analysis_area.insert(tk.END, f"Best Move: {analysis['pv'][0]}\n\n")

    def refresh_board(self):
        self.board_canvas.delete("all")
        for square in chess.SQUARES:
            col, row = chess.square_file(square), chess.square_rank(square)
            if self.board_flipped:
                col, row = 7 - col, 7 - row
            x1, y1 = col * 50, (7 - row) * 50
            x2, y2 = x1 + 50, y1 + 50
            color = "#F0D9B5" if (col + row) % 2 == 0 else "#B58863"
            self.board_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
    
            piece = self.board.piece_at(square)
            if piece:
                piece_image = self.piece_images[piece.symbol()]
                self.board_canvas.create_image(x1, y1, anchor=tk.NW, image=piece_image)
    
        # Highlight the previous move (if any)
        if len(self.board.move_stack) > 0:
            last_move = self.board.move_stack[-1]
            from_square = last_move.from_square
            to_square = last_move.to_square
    
            from_col, from_row = chess.square_file(from_square), chess.square_rank(from_square)
            to_col, to_row = chess.square_file(to_square), chess.square_rank(to_square)
            if self.board_flipped:
                from_col, from_row = 7 - from_col, 7 - from_row
                to_col, to_row = 7 - to_col, 7 - to_row
    
            from_x1, from_y1 = from_col * 50, (7 - from_row) * 50
            from_x2, from_y2 = from_x1 + 50, from_y1 + 50
            to_x1, to_y1 = to_col * 50, (7 - to_row) * 50
            to_x2, to_y2 = to_x1 + 50, to_y1 + 50
    
            self.board_canvas.create_rectangle(from_x1, from_y1, from_x2, from_y2, fill="#FFD700", outline="", stipple="gray50")
            self.board_canvas.create_rectangle(to_x1, to_y1, to_x2, to_y2, fill="#FFFF00", outline="", stipple="gray50")
    
        # Highlight the suggested move (if any)
        analysis = self.engine.analyze(self.board)
        if "pv" in analysis:
            suggested_move = analysis["pv"][0]
            from_square = suggested_move.from_square
            to_square = suggested_move.to_square
    
            from_col, from_row = chess.square_file(from_square), chess.square_rank(from_square)
            to_col, to_row = chess.square_file(to_square), chess.square_rank(to_square)
            if self.board_flipped:
                from_col, from_row = 7 - from_col, 7 - from_row
                to_col, to_row = 7 - to_col, 7 - to_row
    
            from_x1, from_y1 = from_col * 50, (7 - from_row) * 50
            from_x2, from_y2 = from_x1 + 50, from_y1 + 50
            to_x1, to_y1 = to_col * 50, (7 - to_row) * 50
            to_x2, to_y2 = to_x1 + 50, to_y1 + 50
    
            self.board_canvas.create_rectangle(from_x1, from_y1, from_x2, from_y2, fill="#00FF00", outline="", stipple="gray50")
            self.board_canvas.create_rectangle(to_x1, to_y1, to_x2, to_y2, fill="#00FF00", outline="", stipple="gray50")
    
        # Highlight the selected square (if any)
        if self.selected_square is not None:
            col, row = chess.square_file(self.selected_square), chess.square_rank(self.selected_square)
            if self.board_flipped:
                col, row = 7 - col, 7 - row
            x1, y1 = col * 50, (7 - row) * 50
            x2, y2 = x1 + 50, y1 + 50
            self.board_canvas.create_rectangle(
                x1, y1, x2, y2, fill="#FFFF00", outline="", stipple="gray50"
            )
        
        # Update the analysis bar
        self.update_analysis_bar()

    def load_piece_images(self):
        piece_symbols = {
            "P": "wp.png",
            "N": "wn.png",
            "B": "wb.png",
            "R": "wr.png",
            "Q": "wq.png",
            "K": "wk.png",
            "p": "bp.png",
            "n": "bn.png",
            "b": "bb.png",
            "r": "br.png",
            "q": "bq.png",
            "k": "bk.png",
        }
        piece_images = {}
        for symbol, filename in piece_symbols.items():
            image = Image.open(f"assets/piece_images/{filename}")
            piece_images[symbol] = ImageTk.PhotoImage(image.resize((50, 50)))
        return piece_images

    def on_quit(self):
        self.engine.quit()
        self.root.destroy()

    def next_move(self):
        if self.move_stack:
            move = self.move_stack.pop(0)
            self.board.push(move)
            self.refresh_board()
            self.analyze_current_position()
            self.move_history.update(self.board.move_stack)
            self.update_analysis_bar()

    def prev_move(self):
        if self.board.move_stack:
            move = self.board.pop()
            self.move_stack.insert(0, move)
            self.refresh_board()
            self.analyze_current_position()
            self.move_history.update(self.board.move_stack)
            self.update_analysis_bar()
    
    def update_analysis_bar(self):
        analysis = self.engine.analyze(self.board)
        score = analysis["score"]
    
        if self.board.turn == chess.BLACK:
            score = -score  # Invert score if it's black's turn
    
        scaled_score = score / 100  # Scale the score to pawns
    
        # Apply more gradual exponential scaling
        def gradual_exponential_scale(score):
            if score >= 0:
                return 1 - math.exp(-score / 3)  # Adjust the divisor to control scaling
            else:
                return -1 + math.exp(score / 3)  # Adjust the divisor to control scaling
    
        scaled_score = gradual_exponential_scale(scaled_score)
    
        # Cap the scaled score to be within the range [-1, 1]
        if scaled_score > 1:
            scaled_score = 1
        elif scaled_score < -1:
            scaled_score = -1
    
        # Calculate percentages of advantage for white and black
        white_percentage = (scaled_score + 1) * 50
        black_percentage = 100 - white_percentage
    
        # Clear existing bar
        self.analysis_bar.delete("all")
    
        # Draw white and black sections of the bar
        if self.board_flipped:
            self.analysis_bar.create_rectangle(
                0, 0, 20, white_percentage * 4, fill="#FFFFFF", outline=""
            )
            self.analysis_bar.create_rectangle(
                0, white_percentage * 4, 20, 400, fill="#000000", outline=""
            )
        else:
            self.analysis_bar.create_rectangle(
                0, 400 - white_percentage * 4, 20, 400, fill="#FFFFFF", outline=""
            )
            self.analysis_bar.create_rectangle(
                0, 0, 20, 400 - white_percentage * 4, fill="#000000", outline=""
            )
    
        # Handle mate situation
        if abs(score) >= 10000:  # Assuming a score of 10000 or more indicates mate
            if score > 0:
                self.analysis_bar.create_rectangle(
                    0, 0, 20, 400, fill="#FFFFFF", outline=""
                )
            else:
                self.analysis_bar.create_rectangle(
                    0, 0, 20, 400, fill="#000000", outline=""
                )


if __name__ == "__main__":
    root = tk.Tk()
    app = ChessAnalyzerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_quit)
    root.mainloop()
