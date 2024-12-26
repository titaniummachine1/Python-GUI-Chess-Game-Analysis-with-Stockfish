import chess

class MoveGen:
    def __init__(self, board):
        self.board = board
        self.white_drawback = None  # Default drawback for white
        self.black_drawback = None  # Default drawback for black
        self.drawback_functions = {
            "no_diagonal_capture": self.no_diagonal_capture,
            "king_must_capture": self.king_must_capture,
            "no_pawn_moves": self.no_pawn_moves,
        }

    def set_drawback(self, color, drawback):
        """
        Set a single drawback for a specific color.
        :param color: chess.WHITE or chess.BLACK
        :param drawback: Drawback name or None
        """
        if color == chess.WHITE:
            self.white_drawback = drawback
        elif color == chess.BLACK:
            self.black_drawback = drawback

    def get_active_drawback(self):
        """
        Get the active drawback for the current player.
        """
        return self.white_drawback if self.board.turn == chess.WHITE else self.black_drawback

    def get_legal_moves(self):
        """
        Get pseudo-legal moves, ignoring checks.
        """
        return list(self.board.pseudo_legal_moves)

    def get_custom_legal_moves(self):
        """
        Apply the active drawback to filter legal moves.
        """
        legal_moves = self.get_legal_moves()
        active_drawback = self.get_active_drawback()

        if active_drawback and active_drawback in self.drawback_functions:
            legal_moves = self.drawback_functions[active_drawback](legal_moves)

        return legal_moves

    def is_custom_legal_move(self, move):
        """
        Check if a move is legal with the active drawback applied.
        """
        return move in self.get_custom_legal_moves()

    def no_diagonal_capture(self, legal_moves):
        """
        Prohibit capturing diagonally.
        """
        filtered_moves = []
        for move in legal_moves:
            if self.board.piece_at(move.to_square):
                from_file = chess.square_file(move.from_square)
                to_file = chess.square_file(move.to_square)
                from_rank = chess.square_rank(move.from_square)
                to_rank = chess.square_rank(move.to_square)
                if from_file == to_file or from_rank == to_rank:
                    filtered_moves.append(move)
            else:
                filtered_moves.append(move)
        return filtered_moves

    def king_must_capture(self, legal_moves):
        """
        Enforce that the king must capture if possible.
        """
        king_captures = [
            move for move in legal_moves
            if self.board.piece_at(move.to_square)
            and self.board.piece_at(move.from_square).piece_type == chess.KING
        ]
        return king_captures if king_captures else legal_moves

    def no_pawn_moves(self, legal_moves):
        """
        Prohibit all pawn moves.
        """
        return [move for move in legal_moves if self.board.piece_at(move.from_square).piece_type != chess.PAWN]

    def is_checkmate(self):
        return False  # Checkmate does not exist in this variant

    def is_stalemate(self):
        return False  # Stalemate does not exist in this variant

    def is_draw(self):
        return False  # Draw does not exist in this variant

    def is_game_over(self):
        return not self.get_custom_legal_moves() or not self.king_on_board()

    def can_capture_king(self):
        """
        Check if the opponent's king can be captured under the current drawback.
        """
        for move in self.get_custom_legal_moves():
            self.board.push(move)
            if self.board.is_checkmate():
                self.board.pop()
                return True
            self.board.pop()
        return False

    def king_on_board(self):
        """
        Check if the current player's king is still on the board.
        """
        king_square = self.board.king(self.board.turn)
        return king_square is not None
