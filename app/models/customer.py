"""Customer model for fraud detection"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime


class CustomerBase(BaseModel):
    """Base customer model"""
    customer_id: str = Field(..., description="Unique customer identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Customer full name")
    email: Optional[EmailStr] = Field(None, description="Customer email address")
    phone: Optional[str] = Field(None, description="Customer phone number")
    address: Optional[str] = Field(None, description="Customer address")


class CustomerCreate(CustomerBase):
    """Model for creating a new customer"""
    pass


class CustomerUpdate(BaseModel):
    """Model for updating customer information"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    risk_level: Optional[str] = None
    
    @validator('risk_level')
    def validate_risk_level(cls, v):
        if v is not None:
            valid_levels = ['low', 'medium', 'high']
            if v not in valid_levels:
                raise ValueError(f'Risk level must be one of {valid_levels}')
        return v


class CustomerResponse(CustomerBase):
    """Model for customer response"""
    id: int
    risk_level: str = Field(default="low", description="Customer risk level")
    risk_score: float = Field(default=0.0, ge=0, le=10, description="Customer risk score")
    is_blocked: bool = Field(default=False, description="Whether customer is blocked")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class CustomerRiskProfile(BaseModel):
    """Model for customer risk profile"""
    customer_id: str
    risk_score: float = Field(..., ge=0, le=10, description="Overall risk score")
    risk_level: str = Field(..., description="Risk level classification")
    risk_factors: List[str] = Field(default_factory=list, description="Identified risk factors")
    transaction_patterns: dict = Field(default_factory=dict, description="Transaction behavior patterns")
    fraud_history: dict = Field(default_factory=dict, description="Historical fraud incidents")
    last_assessment: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('risk_level')
    def validate_risk_level(cls, v):
        valid_levels = ['low', 'medium', 'high', 'critical']
        if v not in valid_levels:
            raise ValueError(f'Risk level must be one of {valid_levels}')
        return v


class CustomerStatistics(BaseModel):
    """Model for customer statistics"""
    customer_id: str
    total_transactions: int = Field(default=0, description="Total number of transactions")
    total_amount: float = Field(default=0.0, description="Total transaction amount")
    average_transaction: float = Field(default=0.0, description="Average transaction amount")
    flagged_transactions: int = Field(default=0, description="Number of flagged transactions")
    fraud_rate: float = Field(default=0.0, description="Fraud rate percentage")
    last_transaction: Optional[datetime] = Field(None, description="Last transaction date")
    preferred_merchants: List[str] = Field(default_factory=list, description="Most used merchants")
    preferred_channels: List[str] = Field(default_factory=list, description="Most used channels")
    geographic_pattern: dict = Field(default_factory=dict, description="Geographic transaction patterns")
    time_patterns: dict = Field(default_factory=dict, description="Time-based transaction patterns")


class CustomerAlert(BaseModel):
    """Model for customer-related alerts"""
    customer_id: str
    alert_type: str = Field(..., description="Type of alert")
    severity: str = Field(..., description="Alert severity")
    description: str = Field(..., description="Alert description")
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="active", description="Alert status")
    
    @validator('alert_type')
    def validate_alert_type(cls, v):
        valid_types = [
            'risk_level_change',
            'suspicious_pattern',
            'account_takeover',
            'identity_theft',
            'money_laundering',
            'unusual_activity'
        ]
        if v not in valid_types:
            raise ValueError(f'Alert type must be one of {valid_types}')
        return v
    
    @validator('severity')
    def validate_severity(cls, v):
        valid_severities = ['low', 'medium', 'high', 'critical']
        if v not in valid_severities:
            raise ValueError(f'Severity must be one of {valid_severities}')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['active', 'investigating', 'resolved', 'false_positive']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of {valid_statuses}')
        return v


class CustomerFilter(BaseModel):
    """Model for filtering customers"""
    name: Optional[str] = None
    email: Optional[str] = None
    risk_level: Optional[str] = None
    is_blocked: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    has_recent_activity: Optional[bool] = None
    min_risk_score: Optional[float] = Field(None, ge=0, le=10)
    max_risk_score: Optional[float] = Field(None, ge=0, le=10)
    limit: int = Field(default=100, le=1000, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")