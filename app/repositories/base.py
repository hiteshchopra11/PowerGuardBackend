"""Base repository pattern implementation."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Any
from sqlalchemy.orm import Session

T = TypeVar('T')


class BaseRepository(Generic[T], ABC):
    """Base repository providing common database operations."""
    
    def __init__(self, db: Session, model_class):
        self.db = db
        self.model_class = model_class
    
    def get_by_id(self, id: Any) -> Optional[T]:
        """Get entity by ID."""
        return self.db.query(self.model_class).filter(self.model_class.id == id).first()
    
    def get_all(self) -> List[T]:
        """Get all entities."""
        return self.db.query(self.model_class).all()
    
    def create(self, **kwargs) -> T:
        """Create new entity."""
        obj = self.model_class(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def update(self, obj: T, **kwargs) -> T:
        """Update entity."""
        for key, value in kwargs.items():
            setattr(obj, key, value)
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def delete(self, obj: T) -> None:
        """Delete entity."""
        self.db.delete(obj)
        self.db.commit()