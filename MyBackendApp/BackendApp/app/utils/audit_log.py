from sqlalchemy.orm import Session
from ..models.tables import AuditLog
from ..utils.loguru_config import logger

def create_audit_log_entry(user_id: str, action: str, db: Session):
    """
    Create a new audit log entry.
    :param user_id: ID of the user performing the action.
    :param action: Description of the action.
    :param db: Database session.
    """
    try:
        new_audit_log = AuditLog(
            user_id=user_id,
            action=action
        )
        db.add(new_audit_log)
        db.commit()
        logger.info(f"Audit log created for user {user_id}: {action}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create audit log for user {user_id}: {e}")
        raise
