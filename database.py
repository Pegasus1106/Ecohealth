import os
import pathlib
import sqlalchemy as sa
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Create data directory if it doesn't exist
data_dir = pathlib.Path("./data")
data_dir.mkdir(exist_ok=True)
os.chmod(data_dir, 0o777)  # Set directory permissions

# Create SQLite database in the data directory with proper permissions
DATABASE_URL = "sqlite:///./data/newsletter_subscribers.db"

# Configure SQLite engine with proper parameters
engine = create_engine(
    DATABASE_URL, 
    connect_args={
        "check_same_thread": False, 
        "timeout": 30
    },
    # Connections kept in memory for better performance
    poolclass=sa.pool.QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    echo=True  # Log SQL queries for debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Subscriber(Base):
    """Database model for newsletter subscribers"""
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    subscribed_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    location_city = Column(String, nullable=True)
    location_state = Column(String, nullable=True)
    location_country = Column(String, nullable=True)
    last_email_sent = Column(DateTime, nullable=True)

# Create tables
try:
    # Create database file
    if not os.path.exists("./data/newsletter_subscribers.db"):
        open("./data/newsletter_subscribers.db", "w").close()
        os.chmod("./data/newsletter_subscribers.db", 0o666)
        print("Created empty database file with write permissions")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
except Exception as e:
    print(f"Error creating database tables: {str(e)}")
    # Try creating tables with a fresh connection if there was an error
    try:
        # Recreate database file if needed
        if os.path.exists("./data/newsletter_subscribers.db"):
            os.remove("./data/newsletter_subscribers.db")
        open("./data/newsletter_subscribers.db", "w").close()
        os.chmod("./data/newsletter_subscribers.db", 0o666)
        print("Recreated empty database file with write permissions")
        
        # Create tables with a fresh connection
        connection = engine.connect()
        Base.metadata.create_all(bind=connection)
        connection.close()
        print("Database tables created successfully with fresh connection")
    except Exception as e:
        print(f"Fatal error creating database tables: {str(e)}")
        raise

def get_db():
    """Get a database session with automatic retry on failure"""
    from sqlalchemy import text
    
    max_attempts = 3
    attempt = 0
    last_error = None
    db = None
    
    while attempt < max_attempts:
        try:
            db = SessionLocal()
            # Test the connection with proper SQLAlchemy text() function
            db.execute(text("SELECT 1"))
            return db
        except Exception as e:
            last_error = e
            attempt += 1
            print(f"Database connection attempt {attempt} failed: {str(e)}")
            
            # Close the session if it was created
            if db is not None:
                try:
                    db.close()
                    db = None
                except:
                    pass
                
            # Wait before retrying
            if attempt < max_attempts:
                import time
                time.sleep(1)
    
    # If we get here, all attempts failed
    raise Exception(f"Failed to connect to database after {max_attempts} attempts: {str(last_error)}")

def add_subscriber(name, email, city=None, state=None, country=None):
    """Add a new subscriber to the database"""
    db = get_db()
    try:
        # Check if email already exists
        existing = db.query(Subscriber).filter(Subscriber.email == email).first()
        if existing:
            if not existing.is_active:
                # Reactivate if previously unsubscribed
                existing.is_active = True
                existing.name = name
                existing.location_city = city
                existing.location_state = state
                existing.location_country = country
                db.commit()
                return {"success": True, "message": "Subscription reactivated successfully!"}
            return {"success": False, "message": "Email already subscribed"}
        
        # Create new subscriber
        subscriber = Subscriber(
            name=name,
            email=email,
            location_city=city,
            location_state=state,
            location_country=country
        )
        db.add(subscriber)
        db.commit()
        return {"success": True, "message": "Subscribed successfully!"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error adding subscriber: {str(e)}"}
    finally:
        db.close()

def get_active_subscribers():
    """Get all active subscribers"""
    db = get_db()
    try:
        subscribers = db.query(Subscriber).filter(Subscriber.is_active == True).all()
        return subscribers
    finally:
        db.close()

def unsubscribe(email):
    """Unsubscribe a user by email"""
    db = get_db()
    try:
        subscriber = db.query(Subscriber).filter(Subscriber.email == email).first()
        if subscriber:
            subscriber.is_active = False
            db.commit()
            return {"success": True, "message": "Unsubscribed successfully"}
        return {"success": False, "message": "Email not found"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error unsubscribing: {str(e)}"}
    finally:
        db.close()

def update_last_email_sent(email):
    """Update the last_email_sent timestamp for a subscriber"""
    db = get_db()
    try:
        subscriber = db.query(Subscriber).filter(Subscriber.email == email).first()
        if subscriber:
            subscriber.last_email_sent = datetime.utcnow()
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()
        
def delete_subscriber(email):
    """Permanently delete a subscriber by email"""
    db = get_db()
    try:
        subscriber = db.query(Subscriber).filter(Subscriber.email == email).first()
        if subscriber:
            db.delete(subscriber)
            db.commit()
            return {"success": True, "message": f"Subscriber {email} has been permanently deleted"}
        return {"success": False, "message": f"No subscriber found with email: {email}"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error deleting subscriber: {str(e)}"}
    finally:
        db.close()
        
def count_subscribers():
    """Count active and inactive subscribers"""
    db = get_db()
    try:
        active_count = db.query(Subscriber).filter(Subscriber.is_active == True).count()
        inactive_count = db.query(Subscriber).filter(Subscriber.is_active == False).count()
        return {
            "success": True, 
            "total": active_count + inactive_count,
            "active": active_count,
            "inactive": inactive_count
        }
    except Exception as e:
        return {"success": False, "message": f"Error counting subscribers: {str(e)}"}
    finally:
        db.close()
        
def clear_all_subscribers():
    """Delete all subscribers from the database"""
    db = get_db()
    try:
        db.query(Subscriber).delete()
        db.commit()
        return {"success": True, "message": "All subscriber data has been deleted"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error deleting data: {str(e)}"}
    finally:
        db.close()