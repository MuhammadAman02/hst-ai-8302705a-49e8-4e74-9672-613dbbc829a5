"""Database configuration and models for fraud detection"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Database setup
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Customer(Base):
    """Customer information and risk profile"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), index=True)
    phone = Column(String(20))
    address = Column(Text)
    risk_level = Column(String(20), default="low")  # low, medium, high
    risk_score = Column(Float, default=0.0)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    accounts = relationship("Account", back_populates="customer")
    transactions = relationship("Transaction", back_populates="customer")


class Account(Base):
    """Bank account information"""
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String(50), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    account_type = Column(String(20), nullable=False)  # checking, savings, credit
    balance = Column(Numeric(15, 2), default=0.00)
    currency = Column(String(3), default="EUR")
    status = Column(String(20), default="active")  # active, suspended, closed
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")


class Transaction(Base):
    """Transaction records with fraud detection data"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, index=True, nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="EUR")
    transaction_type = Column(String(20), nullable=False)  # debit, credit, transfer
    merchant_name = Column(String(100))
    merchant_category = Column(String(50))
    location_country = Column(String(2))  # ISO country code
    location_city = Column(String(50))
    device_fingerprint = Column(String(100))
    ip_address = Column(String(45))
    channel = Column(String(20))  # online, atm, pos, mobile
    
    # Fraud detection fields
    risk_score = Column(Float, default=0.0)
    is_flagged = Column(Boolean, default=False)
    fraud_indicators = Column(Text)  # JSON string of detected patterns
    
    # Status and timestamps
    status = Column(String(20), default="pending")  # pending, approved, blocked, investigating
    processed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    customer = relationship("Customer", back_populates="transactions")
    alerts = relationship("FraudAlert", back_populates="transaction")


class FraudAlert(Base):
    """Fraud alerts and investigations"""
    __tablename__ = "fraud_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(50), unique=True, index=True, nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    risk_score = Column(Float, nullable=False)
    description = Column(Text)
    fraud_indicators = Column(Text)  # JSON string of specific indicators
    
    # Investigation fields
    status = Column(String(20), default="open")  # open, investigating, resolved, false_positive
    assigned_to = Column(String(50))
    investigation_notes = Column(Text)
    resolution = Column(String(20))  # approved, blocked, escalated
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="alerts")


class RiskRule(Base):
    """Configurable fraud detection rules"""
    __tablename__ = "risk_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), nullable=False)
    rule_type = Column(String(50), nullable=False)  # amount, location, velocity, pattern
    description = Column(Text)
    conditions = Column(Text)  # JSON string of rule conditions
    threshold = Column(Float, nullable=False)
    weight = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AuditLog(Base):
    """Audit trail for compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(50))
    details = Column(Text)  # JSON string of action details
    ip_address = Column(String(45))
    user_agent = Column(String(200))
    timestamp = Column(DateTime, default=func.now())


async def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Create sample data for demonstration
        await create_sample_data()
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def create_sample_data():
    """Create sample data for demonstration"""
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(Customer).first():
            return
        
        # Create sample customers
        customers = [
            Customer(
                customer_id="CUST-001234",
                name="John O'Sullivan",
                email="john.osullivan@email.ie",
                phone="+353-1-234-5678",
                risk_level="high",
                risk_score=8.5
            ),
            Customer(
                customer_id="CUST-001235",
                name="Mary Murphy",
                email="mary.murphy@email.ie",
                phone="+353-1-234-5679",
                risk_level="medium",
                risk_score=5.2
            ),
            Customer(
                customer_id="CUST-001236",
                name="Patrick Kelly",
                email="patrick.kelly@email.ie",
                phone="+353-1-234-5680",
                risk_level="low",
                risk_score=2.1
            )
        ]
        
        for customer in customers:
            db.add(customer)
        
        db.commit()
        
        # Create sample accounts
        accounts = [
            Account(
                account_number="IE29AIBK93115212345678",
                customer_id=1,
                account_type="checking",
                balance=5000.00
            ),
            Account(
                account_number="IE29AIBK93115212345679",
                customer_id=2,
                account_type="savings",
                balance=15000.00
            ),
            Account(
                account_number="IE29AIBK93115212345680",
                customer_id=3,
                account_type="checking",
                balance=2500.00
            )
        ]
        
        for account in accounts:
            db.add(account)
        
        db.commit()
        
        # Create sample transactions
        transactions = [
            Transaction(
                transaction_id="TXN-2024-001234",
                account_id=1,
                customer_id=1,
                amount=2500.00,
                transaction_type="debit",
                merchant_name="Online Electronics Store",
                merchant_category="electronics",
                location_country="IE",
                location_city="Dublin",
                channel="online",
                risk_score=8.5,
                is_flagged=True,
                fraud_indicators='["unusual_amount", "new_merchant", "foreign_ip"]',
                status="investigating"
            ),
            Transaction(
                transaction_id="TXN-2024-001235",
                account_id=2,
                customer_id=2,
                amount=850.00,
                transaction_type="debit",
                merchant_name="Dublin Restaurant",
                merchant_category="dining",
                location_country="IE",
                location_city="Dublin",
                channel="pos",
                risk_score=6.2,
                is_flagged=True,
                fraud_indicators='["velocity_check", "unusual_time"]',
                status="pending"
            ),
            Transaction(
                transaction_id="TXN-2024-001236",
                account_id=3,
                customer_id=3,
                amount=125.50,
                transaction_type="debit",
                merchant_name="Local Grocery Store",
                merchant_category="grocery",
                location_country="IE",
                location_city="Cork",
                channel="pos",
                risk_score=2.1,
                is_flagged=False,
                status="approved"
            )
        ]
        
        for transaction in transactions:
            db.add(transaction)
        
        db.commit()
        
        # Create sample fraud alerts
        alerts = [
            FraudAlert(
                alert_id="FA-2024-001",
                transaction_id=1,
                alert_type="high_risk_transaction",
                severity="high",
                risk_score=8.5,
                description="High-value transaction to new merchant from unusual location",
                fraud_indicators='["unusual_amount", "new_merchant", "foreign_ip"]',
                status="open"
            ),
            FraudAlert(
                alert_id="FA-2024-002",
                transaction_id=2,
                alert_type="velocity_check",
                severity="medium",
                risk_score=6.2,
                description="Multiple transactions in short time period",
                fraud_indicators='["velocity_check", "unusual_time"]',
                status="investigating"
            )
        ]
        
        for alert in alerts:
            db.add(alert)
        
        db.commit()
        logger.info("Sample data created successfully")
        
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()


def get_session() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()