"""Notification service for fraud alerts and system notifications"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import json

from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications about fraud alerts"""
    
    def __init__(self):
        self.email_enabled = settings.EMAIL_ENABLED
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
    
    async def send_fraud_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send fraud alert notification"""
        try:
            # Log the alert
            logger.warning(f"FRAUD ALERT: {alert_data.get('alert_id')} - {alert_data.get('description')}")
            
            # Send email notification if configured
            if self.email_enabled:
                await self._send_email_alert(alert_data)
            
            # Send to monitoring system (placeholder)
            await self._send_to_monitoring_system(alert_data)
            
            # Log to audit trail
            await self._log_notification(alert_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending fraud alert notification: {e}")
            return False
    
    async def _send_email_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send email notification for fraud alert"""
        try:
            if not all([self.smtp_server, self.smtp_username, self.smtp_password]):
                logger.info("Email not configured, skipping email notification")
                return False
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = "fraud-team@irishbank.ie"  # In production, get from config
            msg['Subject'] = f"FRAUD ALERT: {alert_data.get('alert_id')} - {alert_data.get('severity', 'Unknown').upper()}"
            
            # Email body
            body = self._create_email_body(alert_data)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent for {alert_data.get('alert_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            return False
    
    def _create_email_body(self, alert_data: Dict[str, Any]) -> str:
        """Create HTML email body for fraud alert"""
        severity_colors = {
            'low': '#10b981',
            'medium': '#f59e0b',
            'high': '#ef4444',
            'critical': '#dc2626'
        }
        
        severity = alert_data.get('severity', 'medium')
        color = severity_colors.get(severity, '#6b7280')
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f9fafb;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="background-color: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">🚨 Fraud Alert</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">Alert ID: {alert_data.get('alert_id', 'Unknown')}</p>
                </div>
                
                <div style="padding: 20px;">
                    <div style="margin-bottom: 20px;">
                        <h2 style="color: #1f2937; margin: 0 0 10px 0;">Alert Details</h2>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb; font-weight: bold;">Severity:</td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb; color: {color}; font-weight: bold; text-transform: uppercase;">{severity}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb; font-weight: bold;">Risk Score:</td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{alert_data.get('risk_score', 'N/A')}/10</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb; font-weight: bold;">Customer:</td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{alert_data.get('customer_name', 'Unknown')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb; font-weight: bold;">Amount:</td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">€{alert_data.get('amount', 0):,.2f}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb; font-weight: bold;">Merchant:</td>
                                <td style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">{alert_data.get('merchant', 'Unknown')}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Time:</td>
                                <td style="padding: 8px 0;">{alert_data.get('created_at', 'Unknown')}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <h3 style="color: #1f2937; margin: 0 0 10px 0;">Description</h3>
                        <p style="margin: 0; color: #6b7280; line-height: 1.5;">{alert_data.get('description', 'No description available')}</p>
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <h3 style="color: #1f2937; margin: 0 0 10px 0;">Fraud Indicators</h3>
                        <ul style="margin: 0; padding-left: 20px; color: #6b7280;">
                            {''.join([f'<li>{indicator}</li>' for indicator in alert_data.get('fraud_indicators', [])])}
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="http://localhost:8080/dashboard" style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">View in Dashboard</a>
                    </div>
                </div>
                
                <div style="background-color: #f9fafb; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; color: #6b7280; font-size: 14px;">
                    <p style="margin: 0;">Irish Banking Fraud Detection System</p>
                    <p style="margin: 5px 0 0 0;">This is an automated alert. Please investigate immediately.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    async def _send_to_monitoring_system(self, alert_data: Dict[str, Any]) -> bool:
        """Send alert to external monitoring system"""
        try:
            # In production, integrate with monitoring systems like:
            # - Splunk
            # - Datadog
            # - New Relic
            # - Custom SIEM systems
            
            monitoring_payload = {
                'timestamp': datetime.utcnow().isoformat(),
                'alert_type': 'fraud_detection',
                'severity': alert_data.get('severity'),
                'alert_id': alert_data.get('alert_id'),
                'risk_score': alert_data.get('risk_score'),
                'customer_id': alert_data.get('customer_id'),
                'transaction_id': alert_data.get('transaction_id'),
                'amount': alert_data.get('amount'),
                'indicators': alert_data.get('fraud_indicators', [])
            }
            
            # Log to monitoring (placeholder)
            logger.info(f"MONITORING: {json.dumps(monitoring_payload)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending to monitoring system: {e}")
            return False
    
    async def _log_notification(self, alert_data: Dict[str, Any]) -> bool:
        """Log notification to audit trail"""
        try:
            audit_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': 'fraud_alert_notification',
                'alert_id': alert_data.get('alert_id'),
                'severity': alert_data.get('severity'),
                'notification_channels': ['email', 'monitoring', 'audit_log'],
                'status': 'sent'
            }
            
            # In production, store in audit database
            logger.info(f"AUDIT: {json.dumps(audit_entry)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error logging notification: {e}")
            return False
    
    async def send_system_notification(self, message: str, level: str = 'info') -> bool:
        """Send system notification"""
        try:
            notification = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': level,
                'message': message,
                'source': 'fraud_detection_system'
            }
            
            if level in ['error', 'critical']:
                logger.error(f"SYSTEM NOTIFICATION: {message}")
            elif level == 'warning':
                logger.warning(f"SYSTEM NOTIFICATION: {message}")
            else:
                logger.info(f"SYSTEM NOTIFICATION: {message}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending system notification: {e}")
            return False
    
    async def send_compliance_report(self, report_data: Dict[str, Any]) -> bool:
        """Send compliance report notification"""
        try:
            # In production, send to regulatory authorities
            # For Irish banking, this might include:
            # - Central Bank of Ireland
            # - Financial Intelligence Unit (FIU)
            # - European Banking Authority (EBA)
            
            compliance_payload = {
                'timestamp': datetime.utcnow().isoformat(),
                'report_type': report_data.get('report_type'),
                'period': report_data.get('period'),
                'total_alerts': report_data.get('total_alerts'),
                'high_risk_alerts': report_data.get('high_risk_alerts'),
                'blocked_amount': report_data.get('blocked_amount'),
                'submission_required': report_data.get('submission_required', False)
            }
            
            logger.info(f"COMPLIANCE REPORT: {json.dumps(compliance_payload)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending compliance report: {e}")
            return False