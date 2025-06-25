"""Transaction model for fraud detection"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class TransactionBase(BaseModel):
    """Base transaction model"""
    transaction_id: str = Field(..., description="Unique transaction identifier")
    account_id: int = Field(..., description="Account ID")
    customer_id: int = Field(..., description="Customer ID")
    amount: Decimal = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(default="EUR", description="Currency code")
    transaction_type: str = Field(..., description="Transaction type (debit, credit, transfer)")
    merchant_name: Optional[str] = Field(None, description="Merchant name")
    merchant_category: Optional[str] = Field(None, description="Merchant category")
    location_country: str = Field(default="IE", description="Transaction country")
    location_city: Optional[str] = Field(None, description="Transaction city")
    device_fingerprint: Optional[str] = Field(None, description="Device fingerprint")
    ip_address: Optional[str] = Field(None, description="IP address")
    channel: str = Field(default="online", description="Transaction channel")
    
    @validator('currency')
    def validate_currency(cls, v):
        valid_currencies = ['EUR', 'USD', 'GBP']
        if v not in valid_currencies:
            raise ValueError(f'Currency must be one of {valid_currencies}')
        return v
    
    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        valid_types = ['debit', 'credit', 'transfer']
        if v not in valid_types:
            raise ValueError(f'Transaction type must be one of {valid_types}')
        return v
    
    @validator('channel')
    def validate_channel(cls, v):
        valid_channels = ['online', 'atm', 'pos', 'mobile']
        if v not in valid_channels:
            raise ValueError(f'Channel must be one of {valid_channels}')
        return v


class TransactionCreate(TransactionBase):
    """Model for creating a new transaction"""
    pass


class TransactionResponse(TransactionBase):
    """Model for transaction response"""
    id: int
    risk_score: float = Field(default=0.0, description="Fraud risk score (0-10)")
    is_flagged: bool = Field(default=False, description="Whether transaction is flagged for fraud")
    fraud_indicators: List[str] = Field(default_factory=list, description="List of fraud indicators")
    status: str = Field(default="pending", description="Transaction status")
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class TransactionAnalysisRequest(BaseModel):
    """Model for transaction analysis request"""
    transaction_data: TransactionBase
    customer_history: Optional[dict] = Field(None, description="Customer transaction history")
    account_balance: Optional[Decimal] = Field(None, description="Current account balance")
    is_new_merchant: bool = Field(default=False, description="Whether this is a new merchant for the customer")


class TransactionAnalysisResponse(BaseModel):
    """Model for transaction analysis response"""
    transaction_id: str
    risk_score: float = Field(..., ge=0, le=10, description="Risk score from 0-10")
    risk_level: str = Field(..., description="Risk level (low, medium, high, critical)")
    is_flagged: bool = Field(..., description="Whether transaction should be flagged")
    fraud_indicators: List[str] = Field(default_factory=list, description="Detected fraud indicators")
    triggered_rules: List[str] = Field(default_factory=list, description="Triggered fraud rules")
    ml_score: float = Field(..., ge=0, le=10, description="Machine learning model score")
    rule_score: float = Field(..., ge=0, le=10, description="Rule-based score")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    recommended_action: str = Field(..., description="Recommended action (approve, review, block)")
    
    @validator('risk_level')
    def validate_risk_level(cls, v):
        valid_levels = ['low', 'medium', 'high', 'critical']
        if v not in valid_levels:
            raise ValueError(f'Risk level must be one of {valid_levels}')
        return v
    
    @validator('recommended_action')
    def validate_recommended_action(cls, v):
        valid_actions = ['approve', 'review', 'block', 'escalate']
        if v not in valid_actions:
            raise ValueError(f'Recommended action must be one of {valid_actions}')
        return v


class TransactionFilter(BaseModel):
    """Model for filtering transactions"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    customer_id: Optional[int] = None
    account_id: Optional[int] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    risk_level: Optional[str] = None
    status: Optional[str] = None
    is_flagged: Optional[bool] = None
    merchant_category: Optional[str] = None
    location_country: Optional[str] = None
    channel: Optional[str] = None
    limit: int = Field(default=100, le=1000, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")