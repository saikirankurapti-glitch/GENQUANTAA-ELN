from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Naming conventions for constraints to ensure Alembic can properly detect changes and drop/alter constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# The shared metadata instance with naming conventions
metadata = MetaData(naming_convention=convention)

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy 2.0 declarative models.
    All future domain models will inherit from this Base.
    """
    metadata = metadata
