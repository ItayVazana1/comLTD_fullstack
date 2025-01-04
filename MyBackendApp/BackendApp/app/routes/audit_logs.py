from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..models.tables import AuditLog, User
from ..models.database import get_db
from ..utils.loguru_config import logger

router = APIRouter()

# Models for request validation
class AuditLogCreate(BaseModel):
    user_id: str
    action: str

@router.get("/")
def get_audit_logs(db: Session = Depends(get_db)):
    """
    Fetch all audit logs from the database.
    :param db: Database session.
    :return: List of all audit logs.
    """
    logger.info("Fetching all audit logs from the database.")
    audit_logs = db.query(AuditLog).all()
    logger.debug(f"Fetched {len(audit_logs)} audit logs.")
    return audit_logs

@router.get("/{log_id}")
def get_audit_log(log_id: str, db: Session = Depends(get_db)):
    """
    Fetch a specific audit log by its ID.
    :param log_id: The ID of the audit log to fetch.
    :param db: Database session.
    :return: Audit log details.
    """
    logger.info(f"Fetching audit log with ID: {log_id}")
    audit_log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not audit_log:
        logger.warning(f"Audit log with ID {log_id} not found.")
        raise HTTPException(status_code=404, detail="Audit log not found")
    logger.debug(f"Fetched audit log details: {audit_log}")
    return audit_log

@router.get("/user/{user_id}")
def get_audit_logs_by_user(user_id: str, db: Session = Depends(get_db)):
    """
    Fetch all audit logs for a specific user.
    :param user_id: The ID of the user.
    :param db: Database session.
    :return: List of audit logs for the user.
    """
    logger.info(f"Fetching audit logs for user ID: {user_id}")
    audit_logs = db.query(AuditLog).filter(AuditLog.user_id == user_id).all()
    logger.debug(f"Fetched {len(audit_logs)} audit logs for user ID {user_id}.")
    return audit_logs

@router.post("/")
def create_audit_log(audit_log: AuditLogCreate, db: Session = Depends(get_db)):
    """
    Create a new audit log entry in the database.
    :param audit_log: Details of the audit log to create.
    :param db: Database session.
    :return: Details of the created audit log.
    """
    logger.info(f"Creating a new audit log for user ID: {audit_log.user_id}")
    user = db.query(User).filter(User.id == audit_log.user_id).first()
    if not user:
        logger.warning(f"User with ID {audit_log.user_id} not found.")
        raise HTTPException(status_code=404, detail="User not found")

    new_audit_log = AuditLog(
        user_id=audit_log.user_id,
        action=audit_log.action
    )
    db.add(new_audit_log)
    db.commit()
    db.refresh(new_audit_log)
    logger.info(f"Audit log created successfully with ID: {new_audit_log.id}")
    return new_audit_log

@router.get("/actions")
def get_possible_actions():
    """
    Fetch all possible actions for audit logging.
    :return: List of predefined actions.
    """
    logger.info("Fetching possible audit log actions.")
    return [
        "User login",
        "User logout",
        "User registration",
        "Package created",
        "Package updated",
        "Customer deleted",
        "Profile updated",
        # Add more actions as needed
    ]
