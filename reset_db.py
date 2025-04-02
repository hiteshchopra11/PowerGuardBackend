import os
import sqlite3
from app.database import Base, engine

def reset_database():
    """Reset the database by removing the existing file and recreating tables"""
    # Get the database path from the engine URL
    db_path = "power_guard.db"
    
    # Close any existing connections
    engine.dispose()
    
    # Remove the existing database file if it exists
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)
    
    # Create new database and tables
    print("Creating new database and tables...")
    Base.metadata.create_all(bind=engine)
    
    # Set correct permissions (readable and writable)
    os.chmod(db_path, 0o666)
    
    print("Database reset complete!")

if __name__ == "__main__":
    reset_database() 