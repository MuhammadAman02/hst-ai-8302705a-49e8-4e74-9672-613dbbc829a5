"""Alert model for fraud detection"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class AlertBase(BaseModel):
    """Base alert model"""
    alert_id: str = Field(..., description="Unique alert identifier")
    transaction_id: int = Field(..., description="Associated transaction ID")
    alert_type: str = Field(..., description="Type of fraud alert")
    severity: str = Field(..., description="Alert severity level")
    risk_score: float = Field(..., ge=0, le=10, description="Risk score that triggered the alert")
    description: str = Field(..., description="Human-readable alert description")
    fraud_indicators: List[str] = Field(default_factory=list, description="List of fraud indicators")
    
    @validator('alert_type')
    def validate_alert_type(cls, v):
        valid_types = [
            'high_value_transaction',
            'suspicious_location',
            'rapid_transactions',
            'off_hours_transaction',
            'anomaly_detected',
            'velocity_check',
            'pattern_deviation',
            'account_takeover',
            'card_testing',
            'money_laundering'
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


class AlertCreate(AlertBase):
    """Model for creating a new alert"""
    pass


class AlertUpdate(BaseModel):
    """Model for updating an alert"""
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    investigation_notes: Optional[str] = None
    resolution: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ['open', 'investigating', 'resolved', 'false_positive', 'escalated']
            if v not in valid_statuses:
                raise ValueError(f'Status must be one of {valid_statuses}')
        return v
    
    @validator('resolution')
    def validate_resolution(cls, v):
        if v is not None:
            valid_resolutions = ['approved', 'blocked', 'escalated', 'false_positive']
            if v not in valid_resolutions:
                raise ValueError(f'Resolution must be one of {valid_resolutions}')
        return v


class AlertResponse(AlertBase):
    """Model for alert response"""
    id: int
    status: str = Field(default="open", description="Alert status")
    assigned_to: Optional[str] = Field(None, description="User assigned to investigate")
    investigation_notes: Optional[str] = Field(None, description="Investigation notes")
    resolution: Optional[str] = Field(None, description="Alert resolution")
    created_at: datetime
    resolved_at: Optional[datetime] = None
    
    # Related data
    transaction_data: Optional[Dict[str, Any]] = Field(None, description="Associated transaction data")
    customer_data: Optional[Dict[str, Any]] = Field(None, description="Associated customer data")
    
    class Config:
        orm_mode = True


class AlertInvestigation(BaseModel):
    """Model for alert investigation"""
    alert_id: str
    investigator: str = Field(..., description="User conducting investigation")
    investigation_steps: List[Dict[str, Any]] = Field(default_factory=list, description="Investigation steps taken")
    evidence_collected: List[Dict[str, Any]] = Field(default_factory=list, description="Evidence collected")
    risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="Updated risk assessment")
    recommendation: str = Field(..., description="Investigation recommendation")
    confidence_level: float = Field(..., ge=0, le=1, description="Confidence in recommendation")
    investigation_time_minutes: int = Field(default=0, description="Time spent investigating")
    
    @validator('recommendation')
    def validate_recommendation(cls, v):
        valid_recommendations = [
            'approve_transaction',
            'block_transaction',
            'escalate_to_senior',
            'request_customer_verification',
            'monitor_closely',
            'false_positive'
        ]
        if v not in valid_recommendations:
            raise ValueError(f'Recommendation must be one of {valid_recommendations}')
        return v


class AlertStatistics(BaseModel):
    """Model for alert statistics"""
    total_alerts: int = Field(default=0, description="Total number of alerts")
    open_alerts: int = Field(default=0, description="Number of open alerts")
    investigating_alerts: int = Field(default=0, description="Number of alerts under investigation")
    resolved_alerts: int = Field(default=0, description="Number of resolved alerts")
    false_positive_rate: float = Field(default=0.0, description="False positive rate")
    average_resolution_time_hours: float = Field(default=0.0, description="Average time to resolve alerts")
    severity_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution by severity")
    type_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution by alert type")
    monthly_trend: List[Dict[str, Any]] = Field(default_factory=list, description="Monthly alert trends")


class AlertFilter(BaseModel):
    """Model for filtering alerts"""
    alert_type: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    customer_id: Optional[int] = None
    min_risk_score: Optional[float] = Field(None, ge=0, le=10)
    max_risk_score: Optional[float] = Field(None, ge=0, le=10)
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    resolved_after: Optional[datetime] = None
    resolved_before: Optional[datetime] = None
    has_investigation_notes: Optional[bool] = None
    limit: int = Field(default=100, le=1000, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('Sort order must be "asc" or "desc"')
        return v


class AlertNotification(BaseModel):
    """Model for alert notifications"""
    alert_id: str
    notification_type: str = Field(..., description="Type of notification")
    recipients: List[str] = Field(..., description="List of notification recipients")
    channels: List[str] = Field(..., description="Notification channels (email, sms, webhook)")
    message: str = Field(..., description="Notification message")
    priority: str = Field(default="normal", description="Notification priority")
    sent_at: Optional[datetime] = Field(None, description="When notification was sent")
    delivery_status: str = Field(default="pending", description="Delivery status")
    
    @validator('notification_type')
    def validate_notification_type(cls, v):
        valid_types = ['alert_created', 'alert_escalated', 'alert_resolved', 'investigation_required']
        if v not in valid_types:
            raise ValueError(f'Notification type must be one of {valid_types}')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        valid_priorities = ['low', 'normal', 'high', 'urgent']
        if v not in valid_priorities:
            raise ValueError(f'Priority must be one of {valid_priorities}')
        return v
    
    @validator('delivery_status')
    def validate_delivery_status(cls, v):
        valid_statuses = ['pending', 'sent', 'delivered', 'failed', 'bounced']
        if v not in valid_statuses:
            raise ValueError(f'Delivery status must be one of {valid_statuses}')
        return v