from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from ..models.tables import Customer, Package
from ..models.database import get_db
from ..utils.loguru_config import logger
from ..utils.audit_log import create_audit_log_entry

router = APIRouter()

# Models for request validation
class CustomerCreate(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    phone_number: str
    email_address: EmailStr
    address: str
    package_id: str

class CustomerUpdate(BaseModel):
    user_id: str
    first_name: str = None
    last_name: str = None
    phone_number: str = None
    email_address: EmailStr = None
    address: str = None
    package_id: str = None

class UserRequest(BaseModel):
    user_id: str

@router.get("/")
def get_customers(request: UserRequest, db: Session = Depends(get_db)):
    """
    Fetch all customers from the database.
    :param request: UserRequest containing the user ID.
    :param db: Database session.
    :return: List of all customers.
    """
    logger.info(f"Fetching all customers by user {request.user_id}.")
    customers = db.query(Customer).all()
    create_audit_log_entry(user_id=request.user_id, action="Fetched all customers", db=db)
    logger.debug(f"Fetched {len(customers)} customers.")
    return customers

@router.get("/{customer_id}")
def get_customer(customer_id: str, request: UserRequest, db: Session = Depends(get_db)):
    """
    Fetch a specific customer by their ID.
    :param customer_id: The ID of the customer to fetch.
    :param request: UserRequest containing the user ID.
    :param db: Database session.
    :return: Customer details.
    """
    logger.info(f"Fetching customer with ID: {customer_id} by user {request.user_id}.")
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        logger.warning(f"Customer with ID {customer_id} not found.")
        raise HTTPException(status_code=404, detail="Customer not found")
    create_audit_log_entry(user_id=request.user_id, action=f"Fetched customer {customer_id}", db=db)
    logger.debug(f"Fetched customer details: {customer}")
    return customer

@router.post("/")
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    """
    Create a new customer in the database.
    :param customer: Details of the customer to create, including user ID.
    :param db: Database session.
    :return: Details of the created customer.
    """
    logger.info(f"Creating a new customer: {customer.first_name} {customer.last_name} by user {customer.user_id}.")
    package = db.query(Package).filter(Package.id == customer.package_id).first()
    if not package:
        logger.warning(f"Package with ID {customer.package_id} not found.")
        raise HTTPException(status_code=404, detail="Package not found")

    new_customer = Customer(
        first_name=customer.first_name,
        last_name=customer.last_name,
        phone_number=customer.phone_number,
        email_address=customer.email_address,
        address=customer.address,
        package_id=customer.package_id
    )
    db.add(new_customer)

    # Increment subscriber count for the package
    package.subscriber_count += 1

    db.commit()
    db.refresh(new_customer)
    create_audit_log_entry(user_id=customer.user_id, action=f"Created customer {new_customer.id}", db=db)
    logger.info(f"Customer created successfully with ID: {new_customer.id}")
    return new_customer

@router.put("/{customer_id}")
def update_customer(customer_id: str, customer: CustomerUpdate, db: Session = Depends(get_db)):
    """
    Update an existing customer's details in the database.
    :param customer_id: The ID of the customer to update.
    :param customer: Updated details for the customer, including user ID.
    :param db: Database session.
    :return: Updated customer details.
    """
    logger.info(f"Updating customer with ID: {customer_id} by user {customer.user_id}.")
    db_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not db_customer:
        logger.warning(f"Customer with ID {customer_id} not found.")
        raise HTTPException(status_code=404, detail="Customer not found")

    if customer.package_id and customer.package_id != db_customer.package_id:
        # Handle package subscriber count updates
        old_package = db.query(Package).filter(Package.id == db_customer.package_id).first()
        new_package = db.query(Package).filter(Package.id == customer.package_id).first()

        if not new_package:
            logger.warning(f"New package with ID {customer.package_id} not found.")
            raise HTTPException(status_code=404, detail="New package not found")

        if old_package:
            old_package.subscriber_count -= 1

        new_package.subscriber_count += 1
        db_customer.package_id = customer.package_id

    if customer.first_name:
        db_customer.first_name = customer.first_name
    if customer.last_name:
        db_customer.last_name = customer.last_name
    if customer.phone_number:
        db_customer.phone_number = customer.phone_number
    if customer.email_address:
        db_customer.email_address = customer.email_address
    if customer.address:
        db_customer.address = customer.address

    db.commit()
    db.refresh(db_customer)
    create_audit_log_entry(user_id=customer.user_id, action=f"Updated customer {customer_id}", db=db)
    logger.info(f"Customer with ID {customer_id} updated successfully.")
    return db_customer

@router.delete("/{customer_id}")
def delete_customer(customer_id: str, request: UserRequest, db: Session = Depends(get_db)):
    """
    Delete a customer from the database.
    :param customer_id: The ID of the customer to delete.
    :param request: UserRequest containing the user ID.
    :param db: Database session.
    :return: Confirmation of deletion.
    """
    logger.info(f"Deleting customer with ID: {customer_id} by user {request.user_id}.")
    db_customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not db_customer:
        logger.warning(f"Customer with ID {customer_id} not found.")
        raise HTTPException(status_code=404, detail="Customer not found")

    # Handle package subscriber count updates
    if db_customer.package_id:
        package = db.query(Package).filter(Package.id == db_customer.package_id).first()
        if package:
            package.subscriber_count -= 1

    db.delete(db_customer)
    db.commit()
    create_audit_log_entry(user_id=request.user_id, action=f"Deleted customer {customer_id}", db=db)
    logger.info(f"Customer with ID {customer_id} deleted successfully.")
    return {"detail": "Customer deleted successfully"}
