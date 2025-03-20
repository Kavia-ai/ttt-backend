"""SQLAlchemy models for TicTacToe game state persistence."""
from datetime import datetime
from enum import Enum
from typing import List
from sqlalchemy import String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

class DifficultyLevel(str, Enum):
    """Enum for game difficulty levels."""
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'

class GameStatus(str, Enum):
    """Enum for game status."""
    ACTIVE = 'active'
    COMPLETED = 'completed'

class GameOutcome(str, Enum):
    """Enum for game outcomes."""
    WIN = 'win'
    LOSS = 'loss'
    DRAW = 'draw'

# PUBLIC_INTERFACE
class Game(db.Model):
    """Model for storing game state and metadata.
    
    Attributes:
        id: Unique identifier for the game
        board_state: Current state of the game board (9 characters: X, O, or space)
        difficulty: Game difficulty level (easy, medium, hard)
        current_player: Current player's turn (X or O)
        status: Game status (active or completed)
        winner: Winner of the game (X, O, or None)
        outcome: Game outcome (win, loss, draw)
        created_at: Timestamp when the game was created
        updated_at: Timestamp when the game was last updated
        moves: List of moves made in the game
    """
    __tablename__ = 'games'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    board_state: Mapped[str] = mapped_column(String(9), nullable=False, default=' ' * 9)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False, default=DifficultyLevel.MEDIUM)
    current_player: Mapped[str] = mapped_column(String(1), nullable=False, default='X')
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=GameStatus.ACTIVE)
    winner: Mapped[str] = mapped_column(String(1), nullable=True)
    outcome: Mapped[str] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    moves: Mapped[List['GameMove']] = relationship(
        'GameMove',
        back_populates='game',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    # Indexes
    __table_args__ = (
        Index('ix_games_status', 'status'),
        Index('ix_games_difficulty', 'difficulty'),
        Index('ix_games_created_at', 'created_at')
    )

    def __repr__(self) -> str:
        """String representation of the Game model."""
        return f'<Game {self.id} ({self.status})>'

# PUBLIC_INTERFACE
class GameMove(db.Model):
    """Model for storing individual moves in a game.
    
    Attributes:
        id: Unique identifier for the move
        game_id: ID of the game this move belongs to
        position: Board position (0-8)
        player: Player who made the move (X or O)
        created_at: Timestamp when the move was made
        game: Reference to the parent game
    """
    __tablename__ = 'game_moves'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey('games.id'), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    player: Mapped[str] = mapped_column(String(1), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    game: Mapped['Game'] = relationship('Game', back_populates='moves')

    # Indexes
    __table_args__ = (
        Index('ix_game_moves_game_id', 'game_id'),
        Index('ix_game_moves_created_at', 'created_at')
    )

    def __repr__(self) -> str:
        """String representation of the GameMove model."""
        return f'<GameMove {self.id} (Game {self.game_id}, Pos {self.position})>'

# PUBLIC_INTERFACE
class GameStats(db.Model):
    """Model for storing game statistics per difficulty level.
    
    Attributes:
        id: Unique identifier for the stats record
        difficulty: Difficulty level these stats are for
        wins: Number of games won
        losses: Number of games lost
        draws: Number of games drawn
        total_moves: Total number of moves across all games
        created_at: Timestamp when the stats were created
        updated_at: Timestamp when the stats were last updated
    """
    __tablename__ = 'game_stats'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    difficulty: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    losses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    draws: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_moves: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Indexes
    __table_args__ = (
        Index('ix_game_stats_difficulty', 'difficulty', unique=True),
    )

    def __repr__(self) -> str:
        """String representation of the GameStats model."""
        return f'<GameStats {self.difficulty} (W:{self.wins} L:{self.losses} D:{self.draws})>'
