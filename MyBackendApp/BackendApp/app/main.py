from fastapi import FastAPI
from .models.database import engine, load_models
from .models.tables import Base
from .utils.populate import populate_packages
from .routes.users import router as users_router
from .routes.packages import router as packages_router
from .routes.customers import router as customers_router
from .routes.audit_logs import router as audit_logs_router
from .routes.landing_page import router as landing_page_router
from .routes.contact_us import router as contact_us_router
from .utils.loguru_config import logger
from loguru import logger as llog


def create_application() -> FastAPI:
    """
    Function to create the FastAPI application and include all routes and modules.
    """
    logger.info("Initializing application...")
    application = FastAPI(title="Communication LTD API", version="1.0.0")

    # Include routers for all routes
    application.include_router(users_router, prefix="/users", tags=["Users"])
    application.include_router(packages_router, prefix="/packages", tags=["Packages"])
    application.include_router(customers_router, prefix="/customers", tags=["Customers"])
    application.include_router(audit_logs_router, prefix="/audit-logs", tags=["Audit Logs"])
    application.include_router(landing_page_router, tags=["Landing Pages"])
    application.include_router(contact_us_router, tags=["Contact Us"])
    logger.info("Routes registered successfully.")
    llog.info("This is a test log for Loguru!")
    return application


def initialize_database():
    """
    Function to load models, create tables, and populate initial data.
    """
    logger.info("Starting table creation...")
    load_models()
    Base.metadata.create_all(bind=engine)
    populate_packages()
    logger.info("Table creation and data population completed.")


# Initialize database and application
initialize_database()
app = create_application()  # Ensure the 'app' variable is accessible
