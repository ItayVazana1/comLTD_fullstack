from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import uuid4
from pydantic import BaseModel, EmailStr
from ..models.tables import User, PasswordReset, AuditLog
from ..models.database import get_db
from ..utils.loguru_config import logger
from ..utils.audit_log import create_audit_log_entry

router = APIRouter()

# Models
class LoginRequest(BaseModel):
    username_or_email: str
    password: str
    remember_me: bool = False

class LoginResponse(BaseModel):
    id: str
    token: str
    status: str

class RegistrationRequest(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    phone_number: str
    password: str
    confirm_password: str
    accept_terms: bool

class UpdateUserRequest(BaseModel):
    full_name: str = None
    phone_number: str = None
    email: EmailStr = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str
    confirm_password: str

# Endpoints
@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
        Handles user login by validating credentials.
        Generates and returns a session token upon successful authentication.
    """
    logger.info(f"Login request received for: {request.username_or_email}")
    try:
        user = db.query(User).filter(
            (User.email == request.username_or_email) | (User.username == request.username_or_email)
        ).first()

        if not user:
            logger.warning(f"Login failed - user not found: {request.username_or_email}")
            raise HTTPException(status_code=401, detail="Invalid username or password")

        if user.hashed_password != request.password:  # Update with hashed password comparison
            logger.warning(f"Login failed - incorrect password for user: {request.username_or_email}")
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # Token generation
        token = str(uuid4())
        user.current_token = token
        user.is_logged_in = True
        user.last_login = datetime.utcnow()
        db.commit()

        create_audit_log_entry(user_id=user.id, action="User login", db=db)

        logger.info(f"Login successful for user: {user.username}")
        return {"id": user.id, "token": token, "status": "success"}

    except Exception as e:
        db.rollback()
        logger.exception(f"Error during login for {request.username_or_email}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/register")
def register(request: RegistrationRequest, db: Session = Depends(get_db)):
    """
        Handles user registration.
        Creates a new user record in the database with validated data.
    """
    logger.info(f"Registration request received for: {request.username}")
    try:
        if request.password != request.confirm_password:
            logger.warning(f"Registration failed - passwords do not match for user: {request.username}")
            raise HTTPException(status_code=400, detail="Passwords do not match")

        existing_user = db.query(User).filter(
            (User.email == request.email) | (User.username == request.username)
        ).first()
        if existing_user:
            logger.warning(f"Registration failed - user already exists: {request.username}")
            raise HTTPException(status_code=400, detail="User with this email or username already exists")

        new_user = User(
            full_name=request.full_name,
            username=request.username,
            email=request.email,
            phone_number=request.phone_number,
            hashed_password=request.password,
            is_active=True,
            is_logged_in=False,
            current_token=None,
            last_login=None,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        create_audit_log_entry(user_id=new_user.id, action="User registration", db=db)

        logger.info(f"User {new_user.username} registered successfully")
        return {"status": "success", "message": "User registered successfully"}

    except Exception as e:
        db.rollback()
        logger.exception(f"Error during registration for {request.username}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/users/{user_id}")
def update_user(user_id: str, request: UpdateUserRequest, db: Session = Depends(get_db)):
    """
        Updates user details such as full name, phone number, or email.
        Validates and prevents duplicate email usage.
    """
    logger.info(f"Update request received for user: {user_id}")
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        if request.full_name:
            user.full_name = request.full_name
        if request.phone_number:
            user.phone_number = request.phone_number
        if request.email:
            existing_user = db.query(User).filter(User.email == request.email, User.id != user_id).first()
            if existing_user:
                logger.warning(f"Email already in use: {request.email}")
                raise HTTPException(status_code=400, detail="Email already in use")
            user.email = request.email

        db.commit()
        db.refresh(user)

        create_audit_log_entry(user_id=user.id, action="User details updated", db=db)

        logger.info(f"User {user.username} updated successfully")
        return {"status": "success", "message": "User updated successfully"}

    except Exception as e:
        db.rollback()
        logger.exception(f"Error updating user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/password-reset")
def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """
        Initiates a password reset process.
        Generates a reset token for the user and stores it in the database.
    """
    logger.info(f"Password reset request received for: {request.email}")
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            logger.warning(f"Password reset failed - user not found: {request.email}")
            raise HTTPException(status_code=404, detail="User not found")

        reset_token = str(uuid4())
        token_expiry = datetime.utcnow() + timedelta(hours=1)

        password_reset = PasswordReset(
            user_id=user.id,
            reset_token=reset_token,
            token_expiry=token_expiry,
            used=False,
        )
        db.add(password_reset)
        db.commit()

        create_audit_log_entry(user_id=user.id, action="Password reset requested", db=db)

        logger.info(f"Password reset token generated for user: {user.username}")
        return {"status": "success", "reset_token": reset_token, "message": "Password reset token generated"}

    except Exception as e:
        db.rollback()
        logger.exception(f"Error during password reset request for {request.email}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
       Completes the password reset process.
       Validates the reset token and updates the user's password.
    """
    logger.info(f"Password reset attempt with token: {request.reset_token}")
    try:
        password_reset = db.query(PasswordReset).filter(PasswordReset.reset_token == request.reset_token).first()

        if not password_reset or password_reset.used:
            logger.warning("Invalid or used password reset token")
            raise HTTPException(status_code=400, detail="Invalid or used token")

        if password_reset.token_expiry < datetime.utcnow():
            logger.warning("Password reset token expired")
            raise HTTPException(status_code=400, detail="Token expired")

        if request.new_password != request.confirm_password:
            logger.warning("Passwords do not match")
            raise HTTPException(status_code=400, detail="Passwords do not match")

        user = db.query(User).filter(User.id == password_reset.user_id).first()
        if not user:
            logger.error("Associated user not found")
            raise HTTPException(status_code=404, detail="User not found")

        user.hashed_password = request.new_password  # Update with hashed password
        password_reset.used = True

        db.commit()

        create_audit_log_entry(user_id=user.id, action="Password reset successful", db=db)

        logger.info(f"Password reset successful for user: {user.username}")
        return {"status": "success", "message": "Password reset successful"}

    except Exception as e:
        db.rollback()
        logger.exception(f"Error during password reset: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
