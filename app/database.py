from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import sqlalchemy

SQLALCHEMY_DATABASE_URL = "sqlite:///./power_guard.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class UsagePattern(Base):
    __tablename__ = "usage_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    deviceId = Column(String, index=True, nullable=False)
    packageName = Column(String, index=True, nullable=False)
    pattern = Column(Text, nullable=False)
    timestamp = Column(Integer, nullable=False)
    
    # Add a unique constraint on deviceId and packageName
    __table_args__ = (
        # This ensures each deviceId + packageName combination is unique
        # and helps with querying patterns for a specific device
        sqlalchemy.UniqueConstraint('deviceId', 'packageName', name='uix_device_package'),
    )

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 