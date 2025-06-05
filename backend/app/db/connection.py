import motor.motor_asyncio
from beanie import init_beanie
from app.core.config import settings
from app.models.user import User
from app.models.document import Document as DocModel # Renaming to avoid conflict with Beanie's Document
import logging

logger = logging.getLogger(__name__)

async def init_db():
    """
    Initializes the database connection and Beanie ODM.
    """
    logger.info(f"Attempting to connect to MongoDB at {settings.MONGODB_URL}")
    
    client = motor.motor_asyncio.AsyncIOMotorClient(
        settings.MONGODB_URL,
        # You can add other client options here if needed, e.g.,
        # uuidRepresentation="standard",
        # maxPoolSize=100,
        # minPoolSize=10,
    )

    try:
        # Test connection
        await client.admin.command('ping')
        logger.info("Successfully connected to MongoDB.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

    database_name = settings.MONGODB_DATABASE
    if not database_name:
        logger.warning("MONGODB_DATABASE environment variable is not set. Using default 'askrag_dev'.")
        database_name = "askrag_dev"

    logger.info(f"Initializing Beanie with database: {database_name}")

    await init_beanie(
        database=client[database_name],
        document_models=[
            User,
            DocModel,
            "app.models.chat.ChatSession", # Use string path for models to avoid circular imports at init
            # Add other Beanie Document models here as they are created
        ]
    )
    logger.info("Beanie ODM initialized successfully.")

async def close_db_connection():
    """
    Closes the database connection.
    Note: Beanie doesn't require explicit connection closing management for the client usually.
    Motor client might be closed if necessary, but often managed by app lifecycle.
    """
    # motor.motor_asyncio.AsyncIOMotorClient doesn't have a close() method in the way
    # some other drivers do. Connection pooling is typically managed by the driver.
    # If you have a specific client instance you created and want to close:
    # if client:
    #    client.close()
    logger.info("Database connection resources cleaned up (if applicable).")

# Optional: If you need to directly access the motor client or db for non-Beanie operations
# async def get_motor_client() -> motor.motor_asyncio.AsyncIOMotorClient:
#     # This would require storing the client instance globally or passing it around.
#     # For Beanie, direct access is usually not needed for CRUD on Document models.
#     pass

# async def get_motor_database() -> motor.motor_asyncio.AsyncIOMotorDatabase:
#     # Same as above.
#     pass
