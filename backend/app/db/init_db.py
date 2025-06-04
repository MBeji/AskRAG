"""
Database initialization and seeding
"""
import asyncio
import logging
from datetime import datetime
from passlib.context import CryptContext

from .connection import connect_to_mongo, close_mongo_connection, get_database
from .repositories import DocumentRepository, UserRepository, ChatRepository
from ..models.user import UserCreate
from ..core.config import settings

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def init_database():
    """Initialize database with indexes and seed data"""
    try:
        # Connect to database
        await connect_to_mongo()
        logger.info("Connected to MongoDB successfully")
        
        # Initialize repositories
        user_repo = UserRepository()
        document_repo = DocumentRepository()
        chat_repo = ChatRepository()
        
        # Create indexes
        logger.info("Creating database indexes...")
        await user_repo.create_indexes()
        await document_repo.create_indexes()
        await chat_repo.create_indexes()
        logger.info("Database indexes created successfully")
        
        # Seed initial data
        await seed_initial_data()
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def seed_initial_data():
    """Seed database with initial data"""
    user_repo = UserRepository()
    
    # Check if admin user already exists
    admin_user = await user_repo.get_by_email("admin@askrag.com")
    if admin_user:
        logger.info("Admin user already exists, skipping seed data")
        return
    
    try:
        # Create admin user
        admin_password = pwd_context.hash("admin123")
        admin_data = UserCreate(
            email="admin@askrag.com",
            username="admin",
            full_name="AskRAG Administrator",
            password="admin123",  # This will be excluded in create method
            bio="System administrator account"
        )
        
        admin_user = await user_repo.create(admin_data, admin_password)
        
        # Make admin user a superuser
        await user_repo.collection.update_one(
            {"_id": admin_user.id},
            {
                "$set": {
                    "is_superuser": True,
                    "is_verified": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Created admin user: {admin_user.email}")
        
        # Create demo user
        demo_password = pwd_context.hash("demo123")
        demo_data = UserCreate(
            email="demo@askrag.com",
            username="demo",
            full_name="Demo User",
            password="demo123",
            bio="Demo account for testing"
        )
        
        demo_user = await user_repo.create(demo_data, demo_password)
        
        # Verify demo user
        await user_repo.verify_user(str(demo_user.id))
        
        logger.info(f"Created demo user: {demo_user.email}")
        logger.info("Initial seed data created successfully")
        
    except Exception as e:
        logger.error(f"Failed to seed initial data: {e}")
        raise


async def reset_database():
    """Reset database (drop all collections)"""
    try:
        await connect_to_mongo()
        db = get_database()
        
        # Drop all collections
        collections = await db.list_collection_names()
        for collection_name in collections:
            await db.drop_collection(collection_name)
            logger.info(f"Dropped collection: {collection_name}")
        
        logger.info("Database reset completed")
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        raise
    finally:
        await close_mongo_connection()


async def check_database_connection():
    """Check database connection"""
    try:
        await connect_to_mongo()
        db = get_database()
        
        # Ping database
        await db.command("ping")
        logger.info("Database connection is healthy")
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    # Run database initialization
    asyncio.run(init_database())
