"""Database configuration and session management."""
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.game import Game, GameMove, GameStats

def init_db(app):
    """Initialize the database with the Flask application.
    
    Args:
        app: Flask application instance
    """
    # Ensure the instance folder exists
    db_path = app.config.get('SQLITE_DB_PATH')
    if db_path:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # SQLAlchemy is already initialized in create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Initialize game stats for different difficulty levels if they don't exist
        _init_game_stats()

def _init_game_stats() -> None:
    """Initialize game statistics for different difficulty levels if they don't exist."""
    difficulty_levels = ['easy', 'medium', 'hard']
    for difficulty in difficulty_levels:
        if not GameStats.query.filter_by(difficulty=difficulty).first():
            stats = GameStats(difficulty=difficulty)
            db.session.add(stats)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()

# PUBLIC_INTERFACE
def create_game(difficulty: str = 'medium') -> Tuple[Optional[Game], Optional[str]]:
    """Create a new game with the specified difficulty level.
    
    Args:
        difficulty: Difficulty level for the game ('easy', 'medium', or 'hard')
        
    Returns:
        Tuple containing the created game object and error message (if any)
    """
    try:
        game = Game(difficulty=difficulty)
        db.session.add(game)
        db.session.commit()
        return game, None
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, str(e)

# PUBLIC_INTERFACE
def get_game(game_id: int) -> Optional[Game]:
    """Retrieve a game by its ID.
    
    Args:
        game_id: ID of the game to retrieve
        
    Returns:
        Game object if found, None otherwise
    """
    return Game.query.get(game_id)

# PUBLIC_INTERFACE
def update_game(game: Game, board_state: str, current_player: str,
               status: str = None, winner: str = None,
               outcome: str = None) -> Tuple[bool, Optional[str]]:
    """Update game state.
    
    Args:
        game: Game object to update
        board_state: New board state
        current_player: Current player ('X' or 'O')
        status: Game status ('active', 'completed')
        winner: Winner of the game ('X', 'O', or None)
        outcome: Game outcome ('win', 'loss', 'draw')
        
    Returns:
        Tuple of (success boolean, error message if any)
    """
    try:
        game.board_state = board_state
        game.current_player = current_player
        if status:
            game.status = status
        if winner is not None:
            game.winner = winner
        if outcome:
            game.outcome = outcome
            # Update game stats if game is completed
            if outcome in ['win', 'loss', 'draw']:
                update_game_stats(game.difficulty, outcome)
        
        db.session.commit()
        return True, None
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, str(e)

# PUBLIC_INTERFACE
def delete_game(game: Game) -> Tuple[bool, Optional[str]]:
    """Delete a game and its moves.
    
    Args:
        game: Game object to delete
        
    Returns:
        Tuple of (success boolean, error message if any)
    """
    try:
        db.session.delete(game)
        db.session.commit()
        return True, None
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, str(e)

# PUBLIC_INTERFACE
def add_move(game: Game, position: int, player: str) -> Tuple[Optional[GameMove], Optional[str]]:
    """Add a new move to the game.
    
    Args:
        game: Game object
        position: Board position (0-8)
        player: Player making the move ('X' or 'O')
        
    Returns:
        Tuple containing the created move object and error message (if any)
    """
    try:
        move = GameMove(game_id=game.id, position=position, player=player)
        db.session.add(move)
        db.session.commit()
        return move, None
    except SQLAlchemyError as e:
        db.session.rollback()
        return None, str(e)

# PUBLIC_INTERFACE
def get_game_moves(game: Game) -> List[GameMove]:
    """Get all moves for a game in chronological order.
    
    Args:
        game: Game object
        
    Returns:
        List of GameMove objects
    """
    return GameMove.query.filter_by(game_id=game.id).order_by(GameMove.created_at).all()

# PUBLIC_INTERFACE
def get_game_stats(difficulty: str) -> Optional[GameStats]:
    """Get game statistics for a specific difficulty level.
    
    Args:
        difficulty: Difficulty level to get stats for
        
    Returns:
        GameStats object if found, None otherwise
    """
    return GameStats.query.filter_by(difficulty=difficulty).first()

# PUBLIC_INTERFACE
def update_game_stats(difficulty: str, outcome: str) -> Tuple[bool, Optional[str]]:
    """Update game statistics for a specific difficulty level.
    
    Args:
        difficulty: Difficulty level
        outcome: Game outcome ('win', 'loss', 'draw')
        
    Returns:
        Tuple of (success boolean, error message if any)
    """
    try:
        stats = get_game_stats(difficulty)
        if not stats:
            stats = GameStats(difficulty=difficulty)
            db.session.add(stats)
        
        if outcome == 'win':
            stats.wins += 1
        elif outcome == 'loss':
            stats.losses += 1
        elif outcome == 'draw':
            stats.draws += 1
            
        stats.total_moves = GameMove.query.join(Game).filter(
            Game.difficulty == difficulty).count()
        
        db.session.commit()
        return True, None
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, str(e)
