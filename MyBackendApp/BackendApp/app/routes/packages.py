from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..models.tables import Package
from ..models.database import get_db
from pydantic import BaseModel
from ..utils.loguru_config import logger
from ..utils.audit_log import create_audit_log_entry

router = APIRouter()

# Models for request validation
class PackageCreate(BaseModel):
    """
    Model for creating a new package.
    """
    user_id: str
    package_name: str
    description: str
    monthly_price: int


class PackageUpdate(BaseModel):
    """
    Model for updating an existing package.
    """
    user_id: str
    description: str
    monthly_price: int


class UserRequest(BaseModel):
    """
    Model for general requests that include user ID.
    """
    user_id: str


@router.get("/")
def get_packages(request: UserRequest, db: Session = Depends(get_db)):
    """
    Fetch all packages from the database.
    :param request: UserRequest containing the user ID.
    :param db: Database session.
    :return: List of all packages.
    """
    logger.info(f"Fetching all packages by user {request.user_id}.")
    packages = db.query(Package).all()
    create_audit_log_entry(user_id=request.user_id, action="Fetched all packages", db=db)
    logger.debug(f"Fetched {len(packages)} packages.")
    return packages


@router.get("/{package_id}")
def get_package(request: UserRequest, package_id: str, db: Session = Depends(get_db)):
    """
    Fetch a specific package by its ID.
    :param request: UserRequest containing the user ID.
    :param package_id: The ID of the package to fetch.
    :param db: Database session.
    :return: Package details.
    """
    logger.info(f"Fetching package with ID {package_id} by user {request.user_id}.")
    package = db.query(Package).filter(Package.id == package_id).first()
    if not package:
        logger.warning(f"Package with ID {package_id} not found.")
        raise HTTPException(status_code=404, detail="Package not found")
    create_audit_log_entry(user_id=request.user_id, action=f"Fetched package {package_id}", db=db)
    logger.debug(f"Fetched package details: {package}")
    return package


@router.post("/")
def create_package(package: PackageCreate, db: Session = Depends(get_db)):
    """
    Create a new package in the database.
    :param package: Details of the package to create, including user ID.
    :param db: Database session.
    :return: Details of the created package.
    """
    logger.info(f"Creating a new package with name {package.package_name} by user {package.user_id}.")
    new_package = Package(
        package_name=package.package_name,
        description=package.description,
        monthly_price=package.monthly_price,
    )
    db.add(new_package)
    db.commit()
    db.refresh(new_package)
    create_audit_log_entry(user_id=package.user_id, action=f"Created package {new_package.package_name}", db=db)
    logger.info(f"Package created successfully with ID: {new_package.id}")
    return new_package


@router.put("/{package_id}")
def update_package(package_id: str, package: PackageUpdate, db: Session = Depends(get_db)):
    """
    Update an existing package in the database.
    :param package_id: The ID of the package to update.
    :param package: Updated details for the package, including user ID.
    :param db: Database session.
    :return: Updated package details.
    """
    logger.info(f"Updating package with ID {package_id} by user {package.user_id}.")
    db_package = db.query(Package).filter(Package.id == package_id).first()
    if not db_package:
        logger.warning(f"Package with ID {package_id} not found.")
        raise HTTPException(status_code=404, detail="Package not found")
    db_package.description = package.description
    db_package.monthly_price = package.monthly_price
    db.commit()
    db.refresh(db_package)
    create_audit_log_entry(user_id=package.user_id, action=f"Updated package {package_id}", db=db)
    logger.info(f"Package with ID {package_id} updated successfully.")
    return db_package


@router.delete("/{package_id}")
def delete_package(package_id: str, request: UserRequest, db: Session = Depends(get_db)):
    """
    Delete a package from the database.
    :param package_id: The ID of the package to delete.
    :param request: UserRequest containing the user ID.
    :param db: Database session.
    :return: Confirmation of deletion.
    """
    logger.info(f"Deleting package with ID {package_id} by user {request.user_id}.")
    db_package = db.query(Package).filter(Package.id == package_id).first()
    if not db_package:
        logger.warning(f"Package with ID {package_id} not found.")
        raise HTTPException(status_code=404, detail="Package not found")
    db.delete(db_package)
    db.commit()
    create_audit_log_entry(user_id=request.user_id, action=f"Deleted package {package_id}", db=db)
    logger.info(f"Package with ID {package_id} deleted successfully.")
    return {"detail": "Package deleted successfully"}
