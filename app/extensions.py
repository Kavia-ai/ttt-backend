"""Flask extensions initialization."""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass

# Initialize SQLAlchemy with the custom base class
db = SQLAlchemy(model_class=Base)
