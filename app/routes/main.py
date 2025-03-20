from flask import Blueprint, jsonify, request
from http import HTTPStatus
from typing import Dict, Any, Tuple

from app.database import (
    create_game, get_game, update_game, get_game_stats,
    add_move, get_game_moves
)
from app.game_logic import TicTacToeGame, MinimaxAI
from app.models.game import DifficultyLevel, GameStatus, GameOutcome

bp = Blueprint('main', __name__)

def validate_difficulty(difficulty: str) -> Tuple[bool, str]:
    """Validate the difficulty level."""
    try:
        DifficultyLevel(difficulty.lower())
        return True, ""
    except ValueError:
        return False, f"Invalid difficulty level. Must be one of: {[d.value for d in DifficultyLevel]}"

def validate_move_position(position: Any) -> Tuple[bool, str]:
    """Validate the move position."""
    try:
        pos = int(position)
        if 0 <= pos <= 8:
            return True, ""
        return False, "Position must be between 0 and 8"
    except (ValueError, TypeError):
        return False, "Position must be an integer between 0 and 8"

@bp.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "TicTacToe API is running"})

# PUBLIC_INTERFACE
@bp.route('/api/games', methods=['POST'])
def create_new_game():
    """Create a new game with specified difficulty level."""
    data = request.get_json() or {}
    difficulty = data.get('difficulty', 'medium').lower()

    # Validate difficulty
    is_valid, error = validate_difficulty(difficulty)
    if not is_valid:
        return jsonify({"error": error}), HTTPStatus.BAD_REQUEST

    # Create game
    game, error = create_game(difficulty)
    if error:
        return jsonify({"error": error}), HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify({
        "game_id": game.id,
        "board_state": game.board_state,
        "current_player": game.current_player,
        "status": game.status,
        "difficulty": game.difficulty
    }), HTTPStatus.CREATED

# PUBLIC_INTERFACE
@bp.route('/api/games/<int:game_id>/moves', methods=['POST'])
def make_move(game_id: int):
    """Process a player's move and respond with AI's move."""
    # Get game
    game = get_game(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), HTTPStatus.NOT_FOUND
    
    if game.status != GameStatus.ACTIVE:
        return jsonify({"error": "Game is already completed"}), HTTPStatus.BAD_REQUEST

    # Validate move position
    data = request.get_json() or {}
    position = data.get('position')
    is_valid, error = validate_move_position(position)
    if not is_valid:
        return jsonify({"error": error}), HTTPStatus.BAD_REQUEST

    # Process player move
    game_logic = TicTacToeGame(game.board_state)
    if not game_logic.is_valid_move(position, game.current_player):
        return jsonify({"error": "Invalid move: position already taken"}), HTTPStatus.BAD_REQUEST

    # Make player move
    game_logic.make_move(position, game.current_player)
    add_move(game, position, game.current_player)

    # Check for win/draw after player move
    game_over, winner = game_logic.check_winner()
    if game_over:
        status = GameStatus.COMPLETED
        outcome = GameOutcome.WIN if winner else GameOutcome.DRAW
        update_game(
            game,
            game_logic.get_board_state(),
            'O',  # AI's turn but game is over
            status=status,
            winner=winner,
            outcome=outcome
        )
        return jsonify({
            "board_state": game_logic.get_board_state(),
            "status": status,
            "winner": winner,
            "outcome": outcome
        })

    # AI move
    ai = MinimaxAI(game.difficulty)
    ai_position = ai.get_ai_move(game_logic)
    if ai_position is not None:
        game_logic.make_move(ai_position, 'O')
        add_move(game, ai_position, 'O')

        # Check for win/draw after AI move
        game_over, winner = game_logic.check_winner()
        status = GameStatus.COMPLETED if game_over else GameStatus.ACTIVE
        outcome = None
        if game_over:
            outcome = GameOutcome.LOSS if winner else GameOutcome.DRAW

        # Update game state
        update_game(
            game,
            game_logic.get_board_state(),
            'X',  # Back to player's turn
            status=status,
            winner=winner,
            outcome=outcome
        )

        return jsonify({
            "board_state": game_logic.get_board_state(),
            "last_move": ai_position,
            "status": status,
            "winner": winner,
            "outcome": outcome
        })

    return jsonify({"error": "Failed to process AI move"}), HTTPStatus.INTERNAL_SERVER_ERROR

# PUBLIC_INTERFACE
@bp.route('/api/games/<int:game_id>', methods=['GET'])
def get_game_state(game_id: int):
    """Get the current state of a game."""
    game = get_game(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), HTTPStatus.NOT_FOUND

    moves = get_game_moves(game)
    move_history = [{
        "position": move.position,
        "player": move.player,
        "created_at": move.created_at.isoformat()
    } for move in moves]

    return jsonify({
        "game_id": game.id,
        "board_state": game.board_state,
        "current_player": game.current_player,
        "status": game.status,
        "difficulty": game.difficulty,
        "winner": game.winner,
        "outcome": game.outcome,
        "moves": move_history,
        "created_at": game.created_at.isoformat(),
        "updated_at": game.updated_at.isoformat()
    })

# PUBLIC_INTERFACE
@bp.route('/api/stats', methods=['GET'])
def get_statistics():
    """Get game statistics for all difficulty levels."""
    stats = {}
    for difficulty in DifficultyLevel:
        difficulty_stats = get_game_stats(difficulty.value)
        if difficulty_stats:
            stats[difficulty.value] = {
                "total_games": difficulty_stats.wins + difficulty_stats.losses + difficulty_stats.draws,
                "wins": difficulty_stats.wins,
                "losses": difficulty_stats.losses,
                "draws": difficulty_stats.draws,
                "win_rate": round(difficulty_stats.wins / difficulty_stats.total_moves * 100, 2) if difficulty_stats.total_moves > 0 else 0
            }

    return jsonify({"statistics": stats})
