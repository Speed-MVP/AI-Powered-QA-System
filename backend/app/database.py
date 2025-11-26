from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    settings.database_url,
    echo=False,  # Set to True for verbose SQL logging
    pool_pre_ping=True,  # Test connections before using
    pool_size=10,
    max_overflow=20
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for models
Base = declarative_base()


# Dependency for routes
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database
def init_db():
    try:
        logger.info("Creating database tables...")
        
        # Ensure ENUM types exist before creating tables
        with engine.connect() as conn:
            from sqlalchemy import text
            
            # Create all required ENUM types if they don't exist
            enums = [
                ("reviewstatus", ['pending', 'in_review', 'completed', 'disputed']),
                ("userrole", ['admin', 'qa_manager', 'reviewer']),
                ("evaluationstatus", ['pending', 'completed', 'reviewed']),
                ("recordingstatus", ['queued', 'processing', 'completed', 'failed']),
                ("violationseverity", ['critical', 'major', 'minor']),
                ("auditeventtype", [
                    'evaluation_created', 'evaluation_updated', 'evaluation_reviewed',
                    'evaluation_overridden', 'model_changed', 'policy_updated', 'batch_processed'
                ]),
            ]
            
            for enum_name, enum_values in enums:
                values_str = ', '.join([f"'{v}'" for v in enum_values])
                conn.execute(text(f"""
                    DO $$ BEGIN
                        CREATE TYPE {enum_name} AS ENUM ({values_str});
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
            conn.commit()
        
        # Create all tables based on models
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        logger.warning("Database initialization failed, but continuing...")
        # Don't raise the exception - let the app start even if DB is not available

