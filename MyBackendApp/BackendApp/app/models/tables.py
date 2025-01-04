from sqlalchemy import Column, String, Integer, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from uuid import uuid4
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from ..utils.loguru_config import logger

# Base for tables
Base = declarative_base()

# User Table
class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    full_name = Column(String(255), nullable=False)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone_number = Column(String(20), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_logged_in = Column(Boolean, default=False)
    current_token = Column(String(255), nullable=True)
    last_login = Column(DateTime, nullable=True, default=datetime.utcnow)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.debug(f"User model initialized: {self.username}, Email: {self.email}")

# Customer Table
class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    email_address = Column(String(255), nullable=False)
    address = Column(String(255), nullable=True)

    package_id = Column(String(36), ForeignKey("packages.id"), nullable=True)
    package = relationship("Package", back_populates="customers")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.debug(f"Customer model initialized: {self.first_name} {self.last_name}, Email: {self.email_address}")

# Package Table
class Package(Base):
    __tablename__ = "packages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    package_name = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    monthly_price = Column(Integer, nullable=False)
    subscriber_count = Column(Integer, default=0)

    customers = relationship("Customer", back_populates="package")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.debug(f"Package model initialized: {self.package_name}, Price: {self.monthly_price}")

# Audit Logs Table
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    action = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.debug(f"AuditLog initialized for User ID: {self.user_id}, Action: {self.action}")

# Failed Login Attempts Table
class FailedLoginAttempt(Base):
    __tablename__ = "failed_login_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username = Column(String(255), nullable=False)
    ip_address = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.debug(f"FailedLoginAttempt initialized: Username: {self.username}, IP: {self.ip_address}")

# Contact Form Submissions Table
class ContactSubmission(Base):
    __tablename__ = "contact_submissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.debug(f"ContactSubmission initialized: Name: {self.name}, Email: {self.email}")


# Relationships for User Table
User.audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


# Password Reset Table
class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    reset_token = Column(String(255), nullable=False, unique=True)
    token_expiry = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)

    user = relationship("User", back_populates="password_resets")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.debug(f"PasswordReset model initialized for User ID: {self.user_id}")


# Relationship on the User Table
User.password_resets = relationship(
    "PasswordReset",
    order_by=PasswordReset.id,
    back_populates="user",
    cascade="all, delete-orphan"
)
