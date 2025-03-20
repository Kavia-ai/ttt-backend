"""Core game logic for TicTacToe including board management and AI opponent."""
from typing import List, Tuple, Optional
import random

# PUBLIC_INTERFACE
class TicTacToeGame:
    """Main game logic class for TicTacToe.
    
    This class handles board state management, move validation, and win detection.
    The board is represented as a 9-character string, with positions numbered 0-8
    from left to right, top to bottom.
    
    Board positions are arranged as follows:
    0 | 1 | 2
    ---------
    3 | 4 | 5
    ---------
    6 | 7 | 8
    """
    
    EMPTY = ' '
    PLAYER_X = 'X'
    PLAYER_O = 'O'
    
    # Winning combinations (rows, columns, diagonals)
    WINNING_COMBINATIONS = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
        (0, 4, 8), (2, 4, 6)              # Diagonals
    ]
    
    def __init__(self, board_state: str = None):
        """Initialize game board.
        
        Args:
            board_state: Optional 9-character string representing the board.
                        If None, creates an empty board.
                        
        Raises:
            ValueError: If board_state is invalid
        """
        if board_state is None:
            self.board = self.EMPTY * 9
        elif len(board_state) != 9 or not all(c in (self.EMPTY, self.PLAYER_X, self.PLAYER_O) 
                                             for c in board_state):
            raise ValueError("Invalid board state")
        else:
            self.board = board_state
    
    # PUBLIC_INTERFACE
    def make_move(self, position: int, player: str) -> bool:
        """Make a move on the board.
        
        Args:
            position: Board position (0-8)
            player: Player symbol ('X' or 'O')
            
        Returns:
            bool: True if move was valid and made, False otherwise
        """
        if not self.is_valid_move(position, player):
            return False
        
        self.board = self.board[:position] + player + self.board[position + 1:]
        return True
    
    # PUBLIC_INTERFACE
    def is_valid_move(self, position: int, player: str) -> bool:
        """Check if a move is valid.
        
        Args:
            position: Board position (0-8)
            player: Player symbol ('X' or 'O')
            
        Returns:
            bool: True if move is valid, False otherwise
        """
        return (0 <= position <= 8 and 
                player in (self.PLAYER_X, self.PLAYER_O) and 
                self.board[position] == self.EMPTY)
    
    # PUBLIC_INTERFACE
    def check_winner(self) -> Tuple[bool, Optional[str]]:
        """Check if there is a winner or draw.
        
        Returns:
            Tuple[bool, Optional[str]]: (game_over, winner)
            winner is None for draw, or player symbol ('X'/'O') for win
        """
        # Check all winning combinations
        for combo in self.WINNING_COMBINATIONS:
            if (self.board[combo[0]] != self.EMPTY and
                self.board[combo[0]] == self.board[combo[1]] == self.board[combo[2]]):
                return True, self.board[combo[0]]
        
        # Check for draw
        if self.EMPTY not in self.board:
            return True, None
        
        return False, None
    
    # PUBLIC_INTERFACE
    def get_valid_moves(self) -> List[int]:
        """Get list of valid move positions.
        
        Returns:
            List[int]: List of valid move positions (0-8)
        """
        return [i for i, cell in enumerate(self.board) if cell == self.EMPTY]
    
    # PUBLIC_INTERFACE
    def get_board_state(self) -> str:
        """Get current board state.
        
        Returns:
            str: 9-character string representing current board state
        """
        return self.board


# PUBLIC_INTERFACE
class MinimaxAI:
    """AI player implementation using minimax algorithm with alpha-beta pruning.
    
    Supports multiple difficulty levels by adjusting search depth and move randomization.
    The AI evaluates moves based on:
    1. Winning possibilities
    2. Blocking opponent's winning moves
    3. Strategic position values
    4. Number of moves to win
    """
    
    # Position weights for strategic moves (center, corners, edges)
    POSITION_WEIGHTS = [3, 2, 3,  # Corner, Edge, Corner
                       2, 4, 2,  # Edge, Center, Edge
                       3, 2, 3]  # Corner, Edge, Corner
    
    def __init__(self, difficulty: str = 'medium'):
        """Initialize AI with specified difficulty.
        
        Args:
            difficulty: Difficulty level ('easy', 'medium', 'hard')
            
        Raises:
            ValueError: If difficulty is invalid
        """
        self.difficulty = difficulty.lower()
        if self.difficulty not in ('easy', 'medium', 'hard'):
            raise ValueError("Invalid difficulty level")
            
        # Configure AI parameters based on difficulty
        if self.difficulty == 'easy':
            self.max_depth = 2
            self.randomization = 0.4
            self.use_position_weights = False
        elif self.difficulty == 'medium':
            self.max_depth = 4
            self.randomization = 0.2
            self.use_position_weights = True
        else:  # hard
            self.max_depth = 9
            self.randomization = 0.0
            self.use_position_weights = True
    
    # PUBLIC_INTERFACE
    def get_ai_move(self, game: TicTacToeGame) -> Optional[int]:
        """Get AI's next move based on current board state and difficulty.
        
        Args:
            game: Current game state
            
        Returns:
            Optional[int]: Position for next move (0-8), or None if no valid moves
        """
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            return None
            
        # For easy/medium difficulty, sometimes make random moves
        if random.random() < self.randomization:
            return random.choice(valid_moves)
        
        # Use minimax to find best move
        best_score = float('-inf')
        best_moves = []
        
        for move in valid_moves:
            # Try move
            game_copy = TicTacToeGame(game.board)
            game_copy.make_move(move, TicTacToeGame.PLAYER_O)
            
            # Evaluate move
            score = self._minimax(game_copy, self.max_depth, float('-inf'), 
                                float('inf'), False)
                                
            # Apply position weights for medium/hard difficulty
            if self.use_position_weights:
                score += self.POSITION_WEIGHTS[move] * 0.1
            
            # Track best moves
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        
        # Randomly choose from equally good moves
        return random.choice(best_moves)
    
    def _minimax(self, game: TicTacToeGame, depth: int, alpha: float, 
                 beta: float, is_maximizing: bool) -> float:
        """Minimax algorithm implementation with alpha-beta pruning.
        
        Args:
            game: Current game state
            depth: Current search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            is_maximizing: True if maximizing player's turn
            
        Returns:
            float: Score for the current board state
        """
        game_over, winner = game.check_winner()
        
        # Terminal states
        if game_over:
            if winner == TicTacToeGame.PLAYER_O:  # AI wins
                return 100 + depth  # Prefer winning sooner
            elif winner == TicTacToeGame.PLAYER_X:  # Human wins
                return -100 - depth  # Avoid losing sooner
            else:  # Draw
                return 0
        
        if depth == 0:
            return self._evaluate_position(game)
        
        valid_moves = game.get_valid_moves()
        
        if is_maximizing:
            max_score = float('-inf')
            for move in valid_moves:
                game_copy = TicTacToeGame(game.board)
                game_copy.make_move(move, TicTacToeGame.PLAYER_O)
                score = self._minimax(game_copy, depth - 1, alpha, beta, False)
                max_score = max(max_score, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return max_score
        else:
            min_score = float('inf')
            for move in valid_moves:
                game_copy = TicTacToeGame(game.board)
                game_copy.make_move(move, TicTacToeGame.PLAYER_X)
                score = self._minimax(game_copy, depth - 1, alpha, beta, True)
                min_score = min(min_score, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return min_score
    
    def _evaluate_position(self, game: TicTacToeGame) -> float:
        """Evaluate the current board position heuristically.
        
        This method is used when max_depth is reached to estimate position value.
        It considers:
        1. Number of two-in-a-row possibilities
        2. Control of center and corners
        3. Blocking opponent's opportunities
        
        Args:
            game: Current game state
            
        Returns:
            float: Estimated position value
        """
        score = 0.0
        board = game.get_board_state()
        
        # Check each winning combination
        for combo in TicTacToeGame.WINNING_COMBINATIONS:
            line = [board[i] for i in combo]
            
            # Count pieces in line
            ai_count = line.count(TicTacToeGame.PLAYER_O)
            human_count = line.count(TicTacToeGame.PLAYER_X)
            empty_count = line.count(TicTacToeGame.EMPTY)
            
            # Score two-in-a-row opportunities
            if ai_count == 2 and empty_count == 1:
                score += 5.0
            elif human_count == 2 and empty_count == 1:
                score -= 4.0
            # Score single pieces with opportunities
            elif ai_count == 1 and empty_count == 2:
                score += 1.0
            elif human_count == 1 and empty_count == 2:
                score -= 1.0
        
        # Add position weights if enabled
        if self.use_position_weights:
            for pos, weight in enumerate(self.POSITION_WEIGHTS):
                if board[pos] == TicTacToeGame.PLAYER_O:
                    score += 0.3 * weight
                elif board[pos] == TicTacToeGame.PLAYER_X:
                    score -= 0.3 * weight
        
        return score
