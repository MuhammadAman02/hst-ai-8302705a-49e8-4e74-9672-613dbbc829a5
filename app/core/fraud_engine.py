"""Advanced fraud detection engine with ML models"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
import logging
import json

from app.core.config import settings

logger = logging.getLogger(__name__)


class FraudDetectionEngine:
    """Advanced fraud detection engine with multiple ML models"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.risk_rules = []
        self.initialize_models()
        self.load_risk_rules()
    
    def initialize_models(self):
        """Initialize ML models for fraud detection"""
        try:
            # Anomaly detection model
            self.models['anomaly'] = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            
            # Classification model
            self.models['classifier'] = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                class_weight='balanced'
            )
            
            # Feature scalers
            self.scalers['transaction'] = StandardScaler()
            
            # Train models with synthetic data (in production, use historical data)
            self._train_models_with_synthetic_data()
            
            logger.info("Fraud detection models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")
            raise
    
    def _train_models_with_synthetic_data(self):
        """Train models with synthetic data for demonstration"""
        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 10000
        
        # Normal transactions
        normal_data = np.random.normal(0, 1, (int(n_samples * 0.9), 8))
        normal_labels = np.zeros(int(n_samples * 0.9))
        
        # Fraudulent transactions (outliers)
        fraud_data = np.random.normal(3, 2, (int(n_samples * 0.1), 8))
        fraud_labels = np.ones(int(n_samples * 0.1))
        
        # Combine data
        X = np.vstack([normal_data, fraud_data])
        y = np.hstack([normal_labels, fraud_labels])
        
        # Shuffle data
        indices = np.random.permutation(len(X))
        X, y = X[indices], y[indices]
        
        # Scale features
        X_scaled = self.scalers['transaction'].fit_transform(X)
        
        # Train models
        self.models['anomaly'].fit(X_scaled)
        self.models['classifier'].fit(X_scaled, y)
        
        logger.info("Models trained with synthetic data")
    
    def load_risk_rules(self):
        """Load configurable risk rules"""
        self.risk_rules = [
            {
                'name': 'high_amount_threshold',
                'type': 'amount',
                'threshold': 5000.0,
                'weight': 3.0,
                'description': 'Transactions above €5,000'
            },
            {
                'name': 'foreign_transaction',
                'type': 'location',
                'threshold': 1.0,
                'weight': 2.0,
                'description': 'Transactions outside Ireland'
            },
            {
                'name': 'unusual_time',
                'type': 'time',
                'threshold': 1.0,
                'weight': 1.5,
                'description': 'Transactions outside normal hours (22:00-06:00)'
            },
            {
                'name': 'velocity_check',
                'type': 'velocity',
                'threshold': 3.0,
                'weight': 2.5,
                'description': 'More than 3 transactions in 10 minutes'
            },
            {
                'name': 'new_merchant',
                'type': 'pattern',
                'threshold': 1.0,
                'weight': 1.0,
                'description': 'First transaction with merchant'
            }
        ]
    
    def analyze_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a transaction for fraud indicators"""
        try:
            # Extract features
            features = self._extract_features(transaction_data)
            
            # Apply rule-based checks
            rule_score, triggered_rules = self._apply_risk_rules(transaction_data)
            
            # Apply ML models
            ml_score = self._apply_ml_models(features)
            
            # Combine scores
            final_score = self._combine_scores(rule_score, ml_score)
            
            # Determine risk level
            risk_level = self._determine_risk_level(final_score)
            
            # Generate fraud indicators
            fraud_indicators = self._generate_fraud_indicators(triggered_rules, features)
            
            result = {
                'transaction_id': transaction_data.get('transaction_id'),
                'risk_score': round(final_score, 2),
                'risk_level': risk_level,
                'is_flagged': final_score >= settings.FRAUD_THRESHOLD,
                'fraud_indicators': fraud_indicators,
                'triggered_rules': triggered_rules,
                'ml_score': round(ml_score, 2),
                'rule_score': round(rule_score, 2),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Transaction {transaction_data.get('transaction_id')} analyzed: risk_score={final_score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing transaction: {e}")
            return {
                'transaction_id': transaction_data.get('transaction_id'),
                'risk_score': 0.0,
                'risk_level': 'unknown',
                'is_flagged': False,
                'fraud_indicators': [],
                'error': str(e)
            }
    
    def _extract_features(self, transaction_data: Dict[str, Any]) -> np.ndarray:
        """Extract numerical features for ML models"""
        features = []
        
        # Amount (normalized)
        amount = float(transaction_data.get('amount', 0))
        features.append(np.log1p(amount))  # Log transform for amount
        
        # Hour of day
        timestamp = transaction_data.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        features.append(timestamp.hour)
        
        # Day of week
        features.append(timestamp.weekday())
        
        # Channel encoding (online=1, atm=2, pos=3, mobile=4)
        channel_map = {'online': 1, 'atm': 2, 'pos': 3, 'mobile': 4}
        features.append(channel_map.get(transaction_data.get('channel', 'pos'), 3))
        
        # Country risk (Ireland=0, EU=1, Other=2)
        country = transaction_data.get('location_country', 'IE')
        eu_countries = ['IE', 'GB', 'FR', 'DE', 'ES', 'IT', 'NL', 'BE', 'AT', 'PT']
        if country == 'IE':
            country_risk = 0
        elif country in eu_countries:
            country_risk = 1
        else:
            country_risk = 2
        features.append(country_risk)
        
        # Transaction type encoding
        type_map = {'debit': 1, 'credit': 2, 'transfer': 3}
        features.append(type_map.get(transaction_data.get('transaction_type', 'debit'), 1))
        
        # Merchant category risk (high-risk categories get higher scores)
        high_risk_categories = ['gambling', 'crypto', 'cash_advance', 'money_transfer']
        category = transaction_data.get('merchant_category', 'other')
        features.append(2 if category in high_risk_categories else 1)
        
        # Account balance ratio (if available)
        account_balance = float(transaction_data.get('account_balance', 10000))
        balance_ratio = amount / max(account_balance, 1)
        features.append(min(balance_ratio, 2.0))  # Cap at 2.0
        
        return np.array(features).reshape(1, -1)
    
    def _apply_risk_rules(self, transaction_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Apply rule-based fraud detection"""
        total_score = 0.0
        triggered_rules = []
        
        amount = float(transaction_data.get('amount', 0))
        timestamp = transaction_data.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        for rule in self.risk_rules:
            triggered = False
            
            if rule['type'] == 'amount':
                if amount >= rule['threshold']:
                    triggered = True
            
            elif rule['type'] == 'location':
                country = transaction_data.get('location_country', 'IE')
                if country != 'IE':
                    triggered = True
            
            elif rule['type'] == 'time':
                hour = timestamp.hour
                if hour >= 22 or hour <= 6:
                    triggered = True
            
            elif rule['type'] == 'velocity':
                # Simplified velocity check (in production, check against recent transactions)
                # For demo, randomly trigger based on transaction pattern
                if 'rapid' in transaction_data.get('fraud_indicators', ''):
                    triggered = True
            
            elif rule['type'] == 'pattern':
                # Check for new merchant pattern
                if transaction_data.get('is_new_merchant', False):
                    triggered = True
            
            if triggered:
                total_score += rule['weight']
                triggered_rules.append(rule['name'])
        
        # Normalize score to 0-10 range
        normalized_score = min(total_score, 10.0)
        
        return normalized_score, triggered_rules
    
    def _apply_ml_models(self, features: np.ndarray) -> float:
        """Apply ML models for fraud detection"""
        try:
            # Scale features
            features_scaled = self.scalers['transaction'].transform(features)
            
            # Anomaly detection score
            anomaly_score = self.models['anomaly'].decision_function(features_scaled)[0]
            # Convert to 0-10 scale (more negative = more anomalous)
            anomaly_score_normalized = max(0, min(10, (0.5 - anomaly_score) * 5))
            
            # Classification probability
            fraud_probability = self.models['classifier'].predict_proba(features_scaled)[0][1]
            classification_score = fraud_probability * 10
            
            # Combine ML scores
            ml_score = (anomaly_score_normalized + classification_score) / 2
            
            return ml_score
            
        except Exception as e:
            logger.error(f"Error applying ML models: {e}")
            return 0.0
    
    def _combine_scores(self, rule_score: float, ml_score: float) -> float:
        """Combine rule-based and ML scores"""
        # Weighted combination (60% rules, 40% ML)
        combined_score = (rule_score * 0.6) + (ml_score * 0.4)
        return min(combined_score, 10.0)
    
    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level based on score"""
        if score >= 8.0:
            return 'critical'
        elif score >= 6.0:
            return 'high'
        elif score >= 4.0:
            return 'medium'
        else:
            return 'low'
    
    def _generate_fraud_indicators(self, triggered_rules: List[str], features: np.ndarray) -> List[str]:
        """Generate human-readable fraud indicators"""
        indicators = []
        
        # Add rule-based indicators
        rule_descriptions = {
            'high_amount_threshold': 'Unusually high transaction amount',
            'foreign_transaction': 'Transaction outside Ireland',
            'unusual_time': 'Transaction at unusual time',
            'velocity_check': 'Multiple rapid transactions',
            'new_merchant': 'First transaction with this merchant'
        }
        
        for rule in triggered_rules:
            if rule in rule_descriptions:
                indicators.append(rule_descriptions[rule])
        
        # Add ML-based indicators
        if len(features) > 0:
            feature_values = features[0]
            
            # Check specific feature patterns
            if feature_values[0] > 8:  # High log amount
                indicators.append('Amount significantly above normal pattern')
            
            if feature_values[4] == 2:  # Non-EU country
                indicators.append('Transaction from high-risk country')
            
            if feature_values[6] == 2:  # High-risk merchant category
                indicators.append('High-risk merchant category')
        
        return list(set(indicators))  # Remove duplicates
    
    def update_risk_rules(self, new_rules: List[Dict[str, Any]]):
        """Update risk rules configuration"""
        self.risk_rules = new_rules
        logger.info(f"Updated {len(new_rules)} risk rules")
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Get model performance metrics"""
        return {
            'models_loaded': len(self.models),
            'rules_active': len([r for r in self.risk_rules if r.get('active', True)]),
            'last_updated': datetime.utcnow().isoformat(),
            'fraud_threshold': settings.FRAUD_THRESHOLD
        }