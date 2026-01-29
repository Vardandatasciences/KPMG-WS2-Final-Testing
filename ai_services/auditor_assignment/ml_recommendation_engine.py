"""
ML-based Recommendation Engine for Auditor Assignment
Uses actual audit history data for training and predictions
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor, AdaBoostRegressor
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder, StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.linear_model import ElasticNet, Ridge, Lasso
import xgboost as xgb
import joblib
import os
from .database.ai_database_service import AIDatabaseService

logger = logging.getLogger(__name__)

class MLRecommendationEngine:
    """Machine Learning-based recommendation engine for auditor assignment"""
    
    def __init__(self, db_service: AIDatabaseService):
        self.db_service = db_service
        self.logger = logger
        self.auditor_model = None
        self.reviewer_model = None
        self.vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        self.label_encoders = {}
        self.scaler = RobustScaler()  # More robust to outliers
        self.is_trained = False
        self.best_auditor_model = None
        self.best_reviewer_model = None
        
    def train_models(self) -> Dict[str, Any]:
        """Train ML models using historical audit data"""
        try:
            self.logger.info("🤖 Starting ML model training...")
            
            # Get training data
            training_data = self.db_service.get_training_data_for_ml()
            
            if not training_data or len(training_data) < 10:
                self.logger.warning("Insufficient training data for ML models")
                return {
                    'success': False,
                    'error': 'Insufficient training data',
                    'data_points': len(training_data) if training_data else 0
                }
            
            # Convert to DataFrame
            df = pd.DataFrame(training_data)
            
            # Prepare features and targets
            auditor_features, auditor_targets = self._prepare_auditor_training_data(df)
            reviewer_features, reviewer_targets = self._prepare_reviewer_training_data(df)
            
            # Train auditor model
            auditor_result = self._train_auditor_model(auditor_features, auditor_targets)
            
            # Train reviewer model
            reviewer_result = self._train_reviewer_model(reviewer_features, reviewer_targets)
            
            # Save models (now that they're stored in self.auditor_model and self.reviewer_model)
            self._save_models(auditor_result, reviewer_result)
            
            self.is_trained = True
            
            return {
                'success': True,
                'auditor_model_score': auditor_result.get('r2_score', 0),
                'reviewer_model_score': reviewer_result.get('r2_score', 0),
                'training_samples': len(df),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error training ML models: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _prepare_auditor_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for auditor recommendation model"""
        try:
            # Filter for auditor assignments
            auditor_data = df[df['Auditor'].notna()].copy()
            
            if len(auditor_data) == 0:
                return np.array([]), np.array([])
            
            # Create features
            features = []
            targets = []
            
            for _, row in auditor_data.iterrows():
                # Text features (using available columns)
                text_content = f"{row['Title']} {row['Scope']} {row['FrameworkName']}"
                
                # User performance features
                user_metrics = self.db_service.get_audit_performance_metrics(row['Auditor'])
                user_skills = self.db_service.get_user_skills_from_audits(row['Auditor'])
                
                # Feature vector
                feature_vector = [
                    len(text_content),  # Content length
                    user_metrics.get('total_audits', 0),
                    user_metrics.get('completed_audits', 0) or 0,
                    user_metrics.get('approved_audits', 0) or 0,
                    user_metrics.get('avg_completion_days', 0) or 0,
                    user_metrics.get('frameworks_worked', 0),
                    user_metrics.get('audit_types_worked', 0),
                    len(user_skills),  # Number of skills
                    1 if row['AuditType'] == 'I' else 0,  # Internal audit
                    1 if row['Status'] == 'Completed' else 0,  # Completion status
                ]
                
                features.append(feature_vector)
                
                # Target: success score based on status and review
                success_score = 0.0
                status = row.get('Status', '')
                review_status = row.get('ReviewStatus')
                
                # Calculate success score based on status
                if status == 'Completed':
                    if review_status == 1:  # Approved
                        success_score = 1.0
                    elif review_status == 2:  # Under review
                        success_score = 0.7
                    elif review_status == 3:  # Rejected
                        success_score = 0.3
                    else:
                        success_score = 0.5  # Completed but no review status
                elif status == 'Under review':
                    success_score = 0.6
                elif status == 'Work In Progress':
                    success_score = 0.4
                elif status == 'Pending':
                    success_score = 0.2
                else:  # Yet to Start
                    success_score = 0.1
                
                # Adjust score based on completion time if available
                if row['completion_days'] and row['completion_days'] > 0:
                    time_factor = max(0.3, 1 - (row['completion_days'] / 30))  # Penalty for taking too long
                    success_score = success_score * time_factor
                
                targets.append(success_score)
            
            return np.array(features), np.array(targets)
            
        except Exception as e:
            self.logger.error(f"Error preparing auditor training data: {str(e)}")
            return np.array([]), np.array([])
    
    def _prepare_reviewer_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for reviewer recommendation model"""
        try:
            # Filter for reviewer assignments
            reviewer_data = df[df['Reviewer'].notna()].copy()
            
            if len(reviewer_data) == 0:
                return np.array([]), np.array([])
            
            # Create features
            features = []
            targets = []
            
            for _, row in reviewer_data.iterrows():
                # Text features (using available columns)
                text_content = f"{row['Title']} {row['Scope']} {row['FrameworkName']}"
                
                # User performance features
                user_metrics = self.db_service.get_audit_performance_metrics(row['Reviewer'])
                user_skills = self.db_service.get_user_skills_from_audits(row['Reviewer'])
                
                # Feature vector
                feature_vector = [
                    len(text_content),  # Content length
                    user_metrics.get('total_audits', 0),
                    user_metrics.get('completed_audits', 0) or 0,
                    user_metrics.get('approved_audits', 0) or 0,
                    user_metrics.get('avg_completion_days', 0) or 0,
                    user_metrics.get('frameworks_worked', 0),
                    user_metrics.get('audit_types_worked', 0),
                    len(user_skills),  # Number of skills
                    1 if row['AuditType'] == 'I' else 0,  # Internal audit
                    1 if row['ReviewStatus'] == 1 else 0,  # Review approval (1=Approved)
                ]
                
                features.append(feature_vector)
                
                # Target: review success score based on review status
                review_score = 0.0
                review_status = row.get('ReviewStatus')
                status = row.get('Status', '')
                
                # Calculate review score based on review status
                if review_status == 1:  # Approved
                    review_score = 1.0
                elif review_status == 2:  # Under review
                    review_score = 0.6
                elif review_status == 3:  # Rejected
                    review_score = 0.2
                else:
                    # No review status yet, base on audit status
                    if status == 'Completed':
                        review_score = 0.5
                    elif status == 'Under review':
                        review_score = 0.4
                    elif status == 'Work In Progress':
                        review_score = 0.3
                    else:
                        review_score = 0.1
                
                # Adjust score based on completion time if available
                if row['completion_days'] and row['completion_days'] > 0:
                    time_factor = max(0.3, 1 - (row['completion_days'] / 14))  # Penalty for slow reviews
                    review_score = review_score * time_factor
                
                targets.append(review_score)
            
            return np.array(features), np.array(targets)
            
        except Exception as e:
            self.logger.error(f"Error preparing reviewer training data: {str(e)}")
            return np.array([]), np.array([])
    
    def _train_auditor_model(self, features: np.ndarray, targets: np.ndarray) -> Dict[str, Any]:
        """Train auditor recommendation model with advanced model selection"""
        try:
            if len(features) == 0:
                return {'success': False, 'error': 'No training data'}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, targets, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Define multiple models to test
            models = {
                'XGBoost': xgb.XGBRegressor(
                    n_estimators=200,
                    learning_rate=0.05,
                    max_depth=6,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                ),
                'RandomForest': RandomForestRegressor(
                    n_estimators=200,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                ),
                'GradientBoosting': GradientBoostingRegressor(
                    n_estimators=200,
                    learning_rate=0.05,
                    max_depth=6,
                    subsample=0.8,
                    random_state=42
                ),
                'ExtraTrees': ExtraTreesRegressor(
                    n_estimators=200,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                ),
                'SVR': SVR(
                    kernel='rbf',
                    C=1.0,
                    gamma='scale',
                    epsilon=0.01
                ),
                'NeuralNetwork': MLPRegressor(
                    hidden_layer_sizes=(100, 50),
                    activation='relu',
                    solver='adam',
                    alpha=0.001,
                    learning_rate='adaptive',
                    max_iter=500,
                    random_state=42
                ),
                'ElasticNet': ElasticNet(
                    alpha=0.1,
                    l1_ratio=0.5,
                    random_state=42,
                    max_iter=1000
                )
            }
            
            # Test all models and find the best one
            best_model = None
            best_score = -float('inf')
            best_name = ''
            model_scores = {}
            
            for name, model in models.items():
                try:
                    # Train model
                    model.fit(X_train_scaled, y_train)
                    
                    # Evaluate
                    y_pred = model.predict(X_test_scaled)
                    r2 = r2_score(y_test, y_pred)
                    mae = mean_absolute_error(y_test, y_pred)
                    
                    # Cross-validation score
                    cv_scores = cross_val_score(model, X_train_scaled, y_train, 
                                              cv=5, scoring='r2')
                    cv_mean = cv_scores.mean()
                    
                    model_scores[name] = {
                        'r2': r2,
                        'mae': mae,
                        'cv_mean': cv_mean,
                        'cv_std': cv_scores.std()
                    }
                    
                    self.logger.info(f"Model {name}: R²={r2:.3f}, MAE={mae:.3f}, CV={cv_mean:.3f}±{cv_scores.std():.3f}")
                    
                    # Select best model based on R² score
                    if r2 > best_score:
                        best_score = r2
                        best_model = model
                        best_name = name
                        
                except Exception as e:
                    self.logger.warning(f"Error training {name}: {str(e)}")
                    continue
            
            if best_model is None:
                return {'success': False, 'error': 'All models failed to train'}
            
            # Set the best model
            self.auditor_model = best_model
            self.best_auditor_model = best_name
            
            return {
                'success': True,
                'best_model': best_name,
                'r2_score': best_score,
                'model_scores': model_scores,
                'training_samples': len(features)
            }
            
        except Exception as e:
            self.logger.error(f"Error training auditor model: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _train_reviewer_model(self, features: np.ndarray, targets: np.ndarray) -> Dict[str, Any]:
        """Train reviewer recommendation model with advanced model selection"""
        try:
            if len(features) == 0:
                return {'success': False, 'error': 'No training data'}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, targets, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Define multiple models to test
            models = {
                'XGBoost': xgb.XGBRegressor(
                    n_estimators=200,
                    learning_rate=0.05,
                    max_depth=6,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                ),
                'RandomForest': RandomForestRegressor(
                    n_estimators=200,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                ),
                'GradientBoosting': GradientBoostingRegressor(
                    n_estimators=200,
                    learning_rate=0.05,
                    max_depth=6,
                    subsample=0.8,
                    random_state=42
                ),
                'ExtraTrees': ExtraTreesRegressor(
                    n_estimators=200,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                ),
                'SVR': SVR(
                    kernel='rbf',
                    C=1.0,
                    gamma='scale',
                    epsilon=0.01
                ),
                'NeuralNetwork': MLPRegressor(
                    hidden_layer_sizes=(100, 50),
                    activation='relu',
                    solver='adam',
                    alpha=0.001,
                    learning_rate='adaptive',
                    max_iter=500,
                    random_state=42
                ),
                'ElasticNet': ElasticNet(
                    alpha=0.1,
                    l1_ratio=0.5,
                    random_state=42,
                    max_iter=1000
                )
            }
            
            # Test all models and find the best one
            best_model = None
            best_score = -float('inf')
            best_name = ''
            model_scores = {}
            
            for name, model in models.items():
                try:
                    # Train model
                    model.fit(X_train_scaled, y_train)
                    
                    # Evaluate
                    y_pred = model.predict(X_test_scaled)
                    r2 = r2_score(y_test, y_pred)
                    mae = mean_absolute_error(y_test, y_pred)
                    
                    # Cross-validation score
                    cv_scores = cross_val_score(model, X_train_scaled, y_train, 
                                              cv=5, scoring='r2')
                    cv_mean = cv_scores.mean()
                    
                    model_scores[name] = {
                        'r2': r2,
                        'mae': mae,
                        'cv_mean': cv_mean,
                        'cv_std': cv_scores.std()
                    }
                    
                    self.logger.info(f"Model {name}: R²={r2:.3f}, MAE={mae:.3f}, CV={cv_mean:.3f}±{cv_scores.std():.3f}")
                    
                    # Select best model based on R² score
                    if r2 > best_score:
                        best_score = r2
                        best_model = model
                        best_name = name
                        
                except Exception as e:
                    self.logger.warning(f"Error training {name}: {str(e)}")
                    continue
            
            if best_model is None:
                return {'success': False, 'error': 'All models failed to train'}
            
            # Set the best model
            self.reviewer_model = best_model
            self.best_reviewer_model = best_name
            
            return {
                'success': True,
                'best_model': best_name,
                'r2_score': best_score,
                'model_scores': model_scores,
                'training_samples': len(features)
            }
            
        except Exception as e:
            self.logger.error(f"Error training reviewer model: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _save_models(self, auditor_model: Any, reviewer_model: Any):
        """Save trained models to disk"""
        try:
            model_dir = os.path.join(os.path.dirname(__file__), 'models')
            os.makedirs(model_dir, exist_ok=True)
            
            print(f"🔍 Debug - auditor_model type: {type(self.auditor_model)}")
            print(f"🔍 Debug - reviewer_model type: {type(self.reviewer_model)}")
            print(f"🔍 Debug - auditor_model has fit: {hasattr(self.auditor_model, 'fit') if self.auditor_model else False}")
            print(f"🔍 Debug - reviewer_model has fit: {hasattr(self.reviewer_model, 'fit') if self.reviewer_model else False}")
            
            # Save the actual model objects (stored in self.auditor_model and self.reviewer_model)
            if self.auditor_model and hasattr(self.auditor_model, 'fit'):
                joblib.dump(self.auditor_model, os.path.join(model_dir, 'auditor_model.pkl'))
                print(f"✅ Auditor model saved: {self.best_auditor_model}")
            else:
                print("❌ Auditor model not saved - no fit method or model is None")
            
            if self.reviewer_model and hasattr(self.reviewer_model, 'fit'):
                joblib.dump(self.reviewer_model, os.path.join(model_dir, 'reviewer_model.pkl'))
                print(f"✅ Reviewer model saved: {self.best_reviewer_model}")
            else:
                print("❌ Reviewer model not saved - no fit method or model is None")
            
            # Save the scaler
            joblib.dump(self.scaler, os.path.join(model_dir, 'scaler.pkl'))
            print("✅ Scaler saved")
                
        except Exception as e:
            self.logger.error(f"Error saving models: {str(e)}")
    
    def _load_models(self):
        """Load trained models from disk"""
        try:
            model_dir = os.path.join(os.path.dirname(__file__), 'models')
            
            auditor_path = os.path.join(model_dir, 'auditor_model.pkl')
            reviewer_path = os.path.join(model_dir, 'reviewer_model.pkl')
            
            if os.path.exists(auditor_path):
                self.auditor_model = joblib.load(auditor_path)
                self.logger.info("✅ Auditor model loaded from disk")
            
            if os.path.exists(reviewer_path):
                self.reviewer_model = joblib.load(reviewer_path)
                self.logger.info("✅ Reviewer model loaded from disk")
            
            # Load the scaler
            scaler_path = os.path.join(model_dir, 'scaler.pkl')
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                self.logger.info("✅ Scaler loaded from disk")
                
            self.is_trained = True
            self.logger.info(f"🔍 Models loaded - Auditor: {self.auditor_model is not None}, Reviewer: {self.reviewer_model is not None}, Scaler: {self.scaler is not None}")
            
        except Exception as e:
            self.logger.error(f"Error loading models: {str(e)}")
    
    def get_ml_recommendations(self, task_data: Dict[str, Any], field_type: str, max_recommendations: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Get ML-based recommendations for auditor/reviewer assignment"""
        try:
            # Load models if not already loaded
            if not self.is_trained:
                self._load_models()
            
            # Get all users
            users = self.db_service.get_users_for_recommendations()
            
            if not users:
                return {
                    'auditor_recommendations': [],
                    'reviewer_recommendations': []
                }
            
            recommendations = []
            
            for user in users:
                # Create feature vector for this user-task combination
                user_features = self._create_user_task_features(user, task_data)
                
                # Use ML prediction only
                score = 0.0
                ml_prediction_used = False
                
                try:
                    if field_type == 'auditor' and self.auditor_model and self.scaler:
                        # Scale features before prediction
                        user_features_scaled = self.scaler.transform([user_features])
                        raw_score = self.auditor_model.predict(user_features_scaled)[0]
                        if raw_score is not None and not np.isnan(raw_score):
                            score = float(raw_score)
                            ml_prediction_used = True
                            print(f"🔍 ML Prediction for {user['UserName']}: {score}")
                    elif field_type == 'reviewer' and self.reviewer_model and self.scaler:
                        # Scale features before prediction
                        user_features_scaled = self.scaler.transform([user_features])
                        raw_score = self.reviewer_model.predict(user_features_scaled)[0]
                        if raw_score is not None and not np.isnan(raw_score):
                            score = float(raw_score)
                            ml_prediction_used = True
                            print(f"🔍 ML Prediction for {user['UserName']}: {score}")
                except Exception as e:
                    print(f"🔍 ML Prediction failed for {user['UserName']}: {str(e)}")
                    ml_prediction_used = False
                
                # If ML prediction failed, use basic scoring based on user metrics
                if not ml_prediction_used:
                    # Calculate score based on user experience and skills
                    total_audits = user_features[1]
                    frameworks_worked = user_features[5]
                    skills_count = user_features[7]
                    
                    # Base score from experience
                    experience_score = min(0.8, total_audits / 10) if total_audits > 0 else 0.1
                    
                    # Framework expertise score
                    framework_score = min(0.6, frameworks_worked / 5) if frameworks_worked > 0 else 0.2
                    
                    # Skills score
                    skills_score = min(0.4, skills_count / 10) if skills_count > 0 else 0.1
                    
                    # Combine scores
                    score = experience_score + framework_score + skills_score
                    print(f"🔍 Basic Score for {user['UserName']}: {score} (exp: {experience_score}, fw: {framework_score}, skills: {skills_score})")
                
                # Ensure score is between 0 and 1
                score = max(0.1, min(1.0, score))  # Minimum score of 0.1 to avoid 0 scores
                
                # Calculate individual metrics
                experience_match = min(1.0, user_features[1] / 10) if user_features[1] > 0 else 0.3
                skills_match = min(1.0, user_features[7] / 5) if user_features[7] > 0 else 0.2
                availability = 0.8  # Assume available
                domain_expertise = min(1.0, user_features[5] / 3) if user_features[5] > 0 else 0.4
                
                recommendations.append({
                    'user_id': user['UserId'],
                    'user_name': user['UserName'],
                    'score': round(score, 3),
                    'metrics': {
                        'ml_prediction': score if ml_prediction_used else 0,
                        'experience_match': round(experience_match, 3),
                        'skills_match': round(skills_match, 3),
                        'availability': availability,
                        'domain_expertise': round(domain_expertise, 3)
                    }
                })
            
            # Sort by score and take top recommendations
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            top_recommendations = recommendations[:max_recommendations]
            
            print(f"🔍 Final recommendations count: {len(top_recommendations)}")
            for rec in top_recommendations:
                print(f"🔍 {rec['user_name']}: {rec['score']}")
            
            return {
                'auditor_recommendations': top_recommendations,
                'reviewer_recommendations': top_recommendations
            }
            
        except Exception as e:
            self.logger.error(f"Error getting ML recommendations: {str(e)}")
            return {
                'auditor_recommendations': [],
                'reviewer_recommendations': []
            }
    
    def _create_user_task_features(self, user: Dict[str, Any], task_data: Dict[str, Any]) -> List[float]:
        """Create feature vector for user-task combination"""
        try:
            # Get user performance metrics
            user_metrics = self.db_service.get_audit_performance_metrics(user['UserId'])
            user_skills = self.db_service.get_user_skills_from_audits(user['UserId'])
            
            # Create text content (using available fields)
            text_content = f"{task_data.get('title', '')} {task_data.get('description', '')} {task_data.get('scope', '')}"
            
            # Helper function to safely convert to float, handling None and NaN
            def safe_float(value, default=0.0):
                if value is None or (isinstance(value, float) and np.isnan(value)):
                    return default
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default
            
            # Feature vector with safe conversion
            features = [
                len(text_content),  # Content length
                safe_float(user_metrics.get('total_audits'), 0),
                safe_float(user_metrics.get('completed_audits'), 0),
                safe_float(user_metrics.get('approved_audits'), 0),
                safe_float(user_metrics.get('avg_completion_days'), 0),
                safe_float(user_metrics.get('frameworks_worked'), 0),
                safe_float(user_metrics.get('audit_types_worked'), 0),
                len(user_skills),  # Number of skills
                1 if task_data.get('auditType') == 'I' else 0,  # Internal audit
                0,  # Placeholder for completion status
            ]
            
            # Ensure no NaN values
            features = [safe_float(f, 0) for f in features]
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error creating user task features: {str(e)}")
            return [0.0] * 10
    
    def _calculate_basic_score(self, user: Dict[str, Any], task_data: Dict[str, Any]) -> float:
        """Fallback basic scoring when ML models are not available"""
        try:
            base_score = 0.5
            
            # Department factor
            user_department = user.get('Department', '')
            if user_department:
                base_score += 0.1
            
            # Name-based matching
            user_name = (user.get('UserName') or '').lower()
            task_keywords = [
                task_data.get('title', '').lower(),
                task_data.get('description', '').lower(),
                task_data.get('objective', '').lower()
            ]
            
            keyword_matches = 0
            for keyword in task_keywords:
                if keyword and keyword in user_name:
                    keyword_matches += 1
            
            if keyword_matches > 0:
                base_score += 0.2
            
            # Status factor
            status = user.get('Status', '')
            if status == 'Y':
                base_score += 0.1
            
            return max(0.1, min(1.0, base_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating basic score: {str(e)}")
            return 0.5
