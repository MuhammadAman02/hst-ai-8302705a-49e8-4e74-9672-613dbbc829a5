"""Fraud detection service for processing transactions"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import asyncio
from sqlalchemy.orm import Session

from app.core.database import get_session, Transaction, FraudAlert, Customer
from app.core.fraud_engine import FraudDetectionEngine
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class FraudDetectionService:
    """Service for fraud detection and alert management"""
    
    def __init__(self):
        self.fraud_engine = FraudDetectionEngine()
        self.notification_service = NotificationService()
    
    async def process_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a transaction through fraud detection pipeline"""
        try:
            # Analyze transaction for fraud
            analysis_result = self.fraud_engine.analyze_transaction(transaction_data)
            
            # Store transaction in database
            db_transaction = await self._store_transaction(transaction_data, analysis_result)
            
            # Create fraud alert if flagged
            if analysis_result.get('is_flagged', False):
                alert = await self._create_fraud_alert(db_transaction, analysis_result)
                
                # Send notifications for high-risk alerts
                if analysis_result.get('risk_level') in ['high', 'critical']:
                    await self.notification_service.send_fraud_alert(alert)
            
            logger.info(f"Processed transaction {transaction_data.get('transaction_id')}")
            
            return {
                'transaction_id': transaction_data.get('transaction_id'),
                'status': 'processed',
                'risk_assessment': analysis_result,
                'requires_review': analysis_result.get('is_flagged', False)
            }
            
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            return {
                'transaction_id': transaction_data.get('transaction_id'),
                'status': 'error',
                'error': str(e)
            }
    
    async def _store_transaction(self, transaction_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> Transaction:
        """Store transaction in database"""
        db = next(get_session())
        try:
            transaction = Transaction(
                transaction_id=transaction_data.get('transaction_id'),
                account_id=transaction_data.get('account_id', 1),
                customer_id=transaction_data.get('customer_id', 1),
                amount=float(transaction_data.get('amount', 0)),
                currency=transaction_data.get('currency', 'EUR'),
                transaction_type=transaction_data.get('transaction_type', 'debit'),
                merchant_name=transaction_data.get('merchant_name'),
                merchant_category=transaction_data.get('merchant_category'),
                location_country=transaction_data.get('location_country', 'IE'),
                location_city=transaction_data.get('location_city'),
                device_fingerprint=transaction_data.get('device_fingerprint'),
                ip_address=transaction_data.get('ip_address'),
                channel=transaction_data.get('channel', 'online'),
                risk_score=analysis_result.get('risk_score', 0.0),
                is_flagged=analysis_result.get('is_flagged', False),
                fraud_indicators=str(analysis_result.get('fraud_indicators', [])),
                status='investigating' if analysis_result.get('is_flagged') else 'approved',
                processed_at=datetime.utcnow()
            )
            
            db.add(transaction)
            db.commit()
            db.refresh(transaction)
            
            return transaction
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing transaction: {e}")
            raise
        finally:
            db.close()
    
    async def _create_fraud_alert(self, transaction: Transaction, analysis_result: Dict[str, Any]) -> FraudAlert:
        """Create fraud alert for flagged transaction"""
        db = next(get_session())
        try:
            alert_id = f"FA-{datetime.now().strftime('%Y')}-{transaction.id:06d}"
            
            alert = FraudAlert(
                alert_id=alert_id,
                transaction_id=transaction.id,
                alert_type=self._determine_alert_type(analysis_result),
                severity=analysis_result.get('risk_level', 'medium'),
                risk_score=analysis_result.get('risk_score', 0.0),
                description=self._generate_alert_description(analysis_result),
                fraud_indicators=str(analysis_result.get('fraud_indicators', [])),
                status='open'
            )
            
            db.add(alert)
            db.commit()
            db.refresh(alert)
            
            logger.info(f"Created fraud alert {alert_id} for transaction {transaction.transaction_id}")
            
            return alert
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating fraud alert: {e}")
            raise
        finally:
            db.close()
    
    def _determine_alert_type(self, analysis_result: Dict[str, Any]) -> str:
        """Determine alert type based on analysis result"""
        triggered_rules = analysis_result.get('triggered_rules', [])
        
        if 'high_amount_threshold' in triggered_rules:
            return 'high_value_transaction'
        elif 'foreign_transaction' in triggered_rules:
            return 'suspicious_location'
        elif 'velocity_check' in triggered_rules:
            return 'rapid_transactions'
        elif 'unusual_time' in triggered_rules:
            return 'off_hours_transaction'
        else:
            return 'anomaly_detected'
    
    def _generate_alert_description(self, analysis_result: Dict[str, Any]) -> str:
        """Generate human-readable alert description"""
        risk_level = analysis_result.get('risk_level', 'medium')
        risk_score = analysis_result.get('risk_score', 0.0)
        indicators = analysis_result.get('fraud_indicators', [])
        
        description = f"Transaction flagged with {risk_level} risk (score: {risk_score:.1f}). "
        
        if indicators:
            description += f"Indicators: {', '.join(indicators[:3])}"
            if len(indicators) > 3:
                description += f" and {len(indicators) - 3} more"
        
        return description
    
    async def get_active_alerts(self, limit: int = 50, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active fraud alerts"""
        db = next(get_session())
        try:
            query = db.query(FraudAlert).filter(FraudAlert.status.in_(['open', 'investigating']))
            
            if severity:
                query = query.filter(FraudAlert.severity == severity)
            
            alerts = query.order_by(FraudAlert.created_at.desc()).limit(limit).all()
            
            result = []
            for alert in alerts:
                # Get associated transaction and customer info
                transaction = db.query(Transaction).filter(Transaction.id == alert.transaction_id).first()
                customer = None
                if transaction:
                    customer = db.query(Customer).filter(Customer.id == transaction.customer_id).first()
                
                alert_data = {
                    'alert_id': alert.alert_id,
                    'transaction_id': transaction.transaction_id if transaction else None,
                    'customer_name': customer.name if customer else 'Unknown',
                    'amount': float(transaction.amount) if transaction else 0.0,
                    'currency': transaction.currency if transaction else 'EUR',
                    'merchant': transaction.merchant_name if transaction else None,
                    'risk_score': alert.risk_score,
                    'severity': alert.severity,
                    'description': alert.description,
                    'status': alert.status,
                    'created_at': alert.created_at.isoformat(),
                    'fraud_indicators': eval(alert.fraud_indicators) if alert.fraud_indicators else []
                }
                result.append(alert_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
        finally:
            db.close()
    
    async def resolve_alert(self, alert_id: str, resolution: str, notes: str = None, user_id: str = None) -> bool:
        """Resolve a fraud alert"""
        db = next(get_session())
        try:
            alert = db.query(FraudAlert).filter(FraudAlert.alert_id == alert_id).first()
            
            if not alert:
                logger.warning(f"Alert {alert_id} not found")
                return False
            
            alert.status = 'resolved'
            alert.resolution = resolution
            alert.resolved_at = datetime.utcnow()
            
            if notes:
                alert.investigation_notes = notes
            
            if user_id:
                alert.assigned_to = user_id
            
            # Update associated transaction status
            transaction = db.query(Transaction).filter(Transaction.id == alert.transaction_id).first()
            if transaction:
                if resolution == 'approved':
                    transaction.status = 'approved'
                elif resolution == 'blocked':
                    transaction.status = 'blocked'
                elif resolution == 'escalated':
                    transaction.status = 'escalated'
            
            db.commit()
            
            logger.info(f"Resolved alert {alert_id} with resolution: {resolution}")
            
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error resolving alert {alert_id}: {e}")
            return False
        finally:
            db.close()
    
    async def get_fraud_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get fraud detection statistics"""
        db = next(get_session())
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Total transactions
            total_transactions = db.query(Transaction).filter(
                Transaction.created_at >= start_date
            ).count()
            
            # Flagged transactions
            flagged_transactions = db.query(Transaction).filter(
                Transaction.created_at >= start_date,
                Transaction.is_flagged == True
            ).count()
            
            # Active alerts
            active_alerts = db.query(FraudAlert).filter(
                FraudAlert.status.in_(['open', 'investigating'])
            ).count()
            
            # Blocked amount
            blocked_amount = db.query(Transaction).filter(
                Transaction.created_at >= start_date,
                Transaction.status == 'blocked'
            ).with_entities(Transaction.amount).all()
            
            total_blocked = sum(float(amount[0]) for amount in blocked_amount)
            
            # Risk distribution
            risk_distribution = {
                'low': db.query(Transaction).filter(
                    Transaction.created_at >= start_date,
                    Transaction.risk_score < 4.0
                ).count(),
                'medium': db.query(Transaction).filter(
                    Transaction.created_at >= start_date,
                    Transaction.risk_score >= 4.0,
                    Transaction.risk_score < 7.0
                ).count(),
                'high': db.query(Transaction).filter(
                    Transaction.created_at >= start_date,
                    Transaction.risk_score >= 7.0
                ).count()
            }
            
            return {
                'period_days': days,
                'total_transactions': total_transactions,
                'flagged_transactions': flagged_transactions,
                'fraud_rate': (flagged_transactions / max(total_transactions, 1)) * 100,
                'active_alerts': active_alerts,
                'blocked_amount': total_blocked,
                'risk_distribution': risk_distribution,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting fraud statistics: {e}")
            return {}
        finally:
            db.close()