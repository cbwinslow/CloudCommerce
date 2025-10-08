import asyncio
import json
import logging
import pickle
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from letta import LettaClient
from litellm import completion
import joblib
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelType(Enum):
    QUALITY_PREDICTOR = "quality_predictor"
    PRICE_PREDICTOR = "price_predictor"
    CATEGORY_CLASSIFIER = "category_classifier"
    SIMILITY_SCORER = "similarity_scorer"
    FEATURE_EXTRACTOR = "feature_extractor"

class TrainingStatus(Enum):
    PENDING = "pending"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATING = "validating"

@dataclass
class TrainingConfig:
    model_type: ModelType
    features: List[str]
    target: str
    test_size: float = 0.2
    random_state: int = 42
    cross_validation_folds: int = 5
    hyperparameter_tuning: bool = True
    feature_selection: bool = True
    use_text_features: bool = True
    use_categorical_features: bool = True
    use_numerical_features: bool = True
    max_features: int = 1000
    model_params: Dict[str, Any] = None

@dataclass
class TrainingMetrics:
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    rmse: float
    mae: float
    r2_score: float
    cross_val_score: float
    training_time: float
    prediction_time: float
    model_size: int
    feature_importance: Dict[str, float]

@dataclass
class TrainingJob:
    id: str
    model_type: ModelType
    config: TrainingConfig
    status: TrainingStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    metrics: Optional[TrainingMetrics]
    model_path: Optional[str]
    error_message: Optional[str]
    user_id: Optional[str]
    dataset_info: Dict[str, Any]

@dataclass
class QualityModifier:
    id: str
    name: str
    description: str
    model_version: str
    modifier_type: str  # "additive", "multiplicative", "rule_based"
    parameters: Dict[str, Any]
    confidence_threshold: float
    quality_improvement: float
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class ModelTrainer:
    def __init__(self, supabase_client, letta_client: LettaClient):
        self.supabase = supabase_client
        self.letta = letta_client
        self.session: Optional[aiohttp.ClientSession] = None
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, Any] = {}
        self.encoders: Dict[str, Any] = {}
        self.vectorizers: Dict[str, Any] = {}
        self.training_jobs: Dict[str, TrainingJob] = {}
        self.quality_modifiers: Dict[str, QualityModifier] = {}
        
        # Initialize agent IDs
        self.agent_ids = {
            "training": os.getenv("LETTA_TRAINING_AGENT_ID"),
            "quality": os.getenv("LETTA_QUALITY_AGENT_ID"),
            "metadata": os.getenv("LETTA_METADATA_AGENT_ID")
        }
        
        # Default configurations
        self.default_configs = {
            ModelType.QUALITY_PREDICTOR: TrainingConfig(
                model_type=ModelType.QUALITY_PREDICTOR,
                features=["title_length", "description_length", "image_count", "price", "category_encoded", "brand_encoded"],
                target="quality_score",
                test_size=0.2,
                hyperparameter_tuning=True,
                feature_selection=True
            ),
            ModelType.PRICE_PREDICTOR: TrainingConfig(
                model_type=ModelType.PRICE_PREDICTOR,
                features=["title_length", "description_length", "image_count", "category_encoded", "brand_encoded", "condition_encoded"],
                target="price",
                test_size=0.2,
                hyperparameter_tuning=True,
                feature_selection=True
            ),
            ModelType.CATEGORY_CLASSIFIER: TrainingConfig(
                model_type=ModelType.CATEGORY_CLASSIFIER,
                features=["title", "description", "keywords"],
                target="category",
                test_size=0.2,
                use_text_features=True,
                use_categorical_features=True,
                use_numerical_features=False
            ),
            ModelType.SIMILITY_SCORER: TrainingConfig(
                model_type=ModelType.SIMILITY_SCORER,
                features=["title_similarity", "description_similarity", "category_match", "price_ratio", "brand_match"],
                target="similarity_score",
                test_size=0.2,
                hyperparameter_tuning=True
            )
        }
    
    async def train_model(self, model_type: ModelType, config: TrainingConfig = None, user_id: str = None) -> TrainingJob:
        """Train a model with the specified configuration"""
        try:
            # Create training job
            job_id = hashlib.md5(f"{model_type.value}_{datetime.now().isoformat()}_{user_id}".encode()).hexdigest()
            job = TrainingJob(
                id=job_id,
                model_type=model_type,
                config=config or self.default_configs.get(model_type),
                status=TrainingStatus.PENDING,
                created_at=datetime.now(),
                user_id=user_id,
                dataset_info={}
            )
            
            self.training_jobs[job_id] = job
            
            # Start training asynchronously
            asyncio.create_task(self._train_model_async(job_id))
            
            return job
            
        except Exception as e:
            logger.error(f"Error starting training job: {e}")
            raise
    
    async def _train_model_async(self, job_id: str):
        """Asynchronous model training"""
        try:
            job = self.training_jobs[job_id]
            job.status = TrainingStatus.TRAINING
            job.started_at = datetime.now()
            
            # Load training data
            training_data = await self._load_training_data(job.config.model_type)
            
            if not training_data:
                raise Exception("No training data available")
            
            # Prepare features and target
            X, y = await self._prepare_training_data(training_data, job.config)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=job.config.test_size, random_state=job.config.random_state
            )
            
            # Train model
            model, metrics = await self._train_model(X_train, y_train, X_test, y_test, job.config)
            
            # Validate model
            validation_metrics = await self._validate_model(model, X_test, y_test, job.config)
            
            # Combine metrics
            combined_metrics = {**metrics, **validation_metrics}
            
            # Save model
            model_path = await self._save_model(model, job.config.model_type, job_id)
            
            # Update job
            job.status = TrainingStatus.COMPLETED
            job.completed_at = datetime.now()
            job.metrics = TrainingMetrics(**combined_metrics)
            job.model_path = model_path
            
            # Store model in memory
            self.models[job_id] = model
            
            logger.info(f"Training completed for job {job_id}")
            
        except Exception as e:
            logger.error(f"Error in training job {job_id}: {e}")
            job.status = TrainingStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
    
    async def _load_training_data(self, model_type: ModelType) -> List[Dict[str, Any]]:
        """Load training data from database"""
        try:
            # Query database based on model type
            if model_type == ModelType.QUALITY_PREDICTOR:
                response = await self.supabase.from("crawled_items").select("*").gte("quality_score", 0).execute()
            elif model_type == ModelType.PRICE_PREDICTOR:
                response = await self.supabase.from("crawled_items").select("*").gt("price", 0).execute()
            elif model_type == ModelType.CATEGORY_CLASSIFIER:
                response = await self.supabase.from("crawled_items").select("*").neq("category", "").execute()
            elif model_type == ModelType.SIMILITY_SCORER:
                response = await self.supabase.from("search_index").select("*").gte("quality_score", 0.5).execute()
            else:
                response = await self.supabase.from("crawled_items").select("*").execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
            return []
    
    async def _prepare_training_data(self, data: List[Dict[str, Any]], config: TrainingConfig) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data features and target"""
        try:
            # Extract features
            features = []
            targets = []
            
            for item in data:
                # Extract feature values
                feature_vector = []
                
                for feature_name in config.features:
                    if feature_name in item:
                        value = item[feature_name]
                        feature_vector.append(value)
                    else:
                        # Handle missing features
                        feature_vector.append(0)
                
                features.append(feature_vector)
                targets.append(item.get(config.target, 0))
            
            # Convert to numpy arrays
            X = np.array(features)
            y = np.array(targets)
            
            # Handle text features
            if config.use_text_features:
                X = await self._add_text_features(X, data, config)
            
            # Handle categorical features
            if config.use_categorical_features:
                X = await self._add_categorical_features(X, data, config)
            
            # Handle numerical features
            if config.use_numerical_features:
                X = await self._add_numerical_features(X, data, config)
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Store scaler
            scaler_key = f"{config.model_type.value}_scaler"
            self.scalers[scaler_key] = scaler
            
            return X_scaled, y
            
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            raise
    
    async def _add_text_features(self, X: np.ndarray, data: List[Dict[str, Any]], config: TrainingConfig) -> np.ndarray:
        """Add text-based features using TF-IDF"""
        try:
            # Combine text fields
            texts = []
            for item in data:
                text_parts = []
                
                # Add title
                if item.get("title"):
                    text_parts.append(item["title"])
                
                # Add description
                if item.get("description"):
                    text_parts.append(item["description"])
                
                # Add keywords
                if item.get("keywords"):
                    text_parts.extend(item["keywords"])
                
                combined_text = " ".join(text_parts)
                texts.append(combined_text)
            
            # Create TF-IDF features
            vectorizer = TfidfVectorizer(max_features=config.max_features, stop_words='english')
            text_features = vectorizer.fit_transform(texts)
            
            # Store vectorizer
            vectorizer_key = f"{config.model_type.value}_vectorizer"
            self.vectorizers[vectorizer_key] = vectorizer
            
            # Combine with existing features
            X_combined = np.hstack([X, text_features.toarray()])
            
            return X_combined
            
        except Exception as e:
            logger.error(f"Error adding text features: {e}")
            return X
    
    async def _add_categorical_features(self, X: np.ndarray, data: List[Dict[str, Any]], config: TrainingConfig) -> np.ndarray:
        """Add categorical features using label encoding"""
        try:
            # Handle categorical features
            categorical_features = ["category", "brand", "condition", "platform"]
            
            for feature_name in categorical_features:
                if feature_name in config.features:
                    # Get unique values
                    unique_values = list(set(item.get(feature_name, "") for item in data))
                    
                    # Create label encoder
                    encoder = LabelEncoder()
                    encoder.fit(unique_values)
                    
                    # Encode values
                    encoded_values = encoder.transform([item.get(feature_name, "") for item in data])
                    
                    # Add to features
                    X = np.column_stack([X, encoded_values])
                    
                    # Store encoder
                    encoder_key = f"{config.model_type.value}_{feature_name}_encoder"
                    self.encoders[encoder_key] = encoder
            
            return X
            
        except Exception as e:
            logger.error(f"Error adding categorical features: {e}")
            return X
    
    async def _add_numerical_features(self, X: np.ndarray, data: List[Dict[str, Any]], config: TrainingConfig) -> np.ndarray:
        """Add numerical features"""
        try:
            # Add derived numerical features
            numerical_features = []
            
            for item in data:
                # Title length
                title_length = len(item.get("title", ""))
                
                # Description length
                desc_length = len(item.get("description", ""))
                
                # Image count
                image_count = len(item.get("images", []))
                
                # Keyword count
                keyword_count = len(item.get("keywords", []))
                
                # Feature count
                feature_count = len(item.get("features", []))
                
                numerical_features.append([title_length, desc_length, image_count, keyword_count, feature_count])
            
            # Add to existing features
            X_numerical = np.array(numerical_features)
            X_combined = np.hstack([X, X_numerical])
            
            return X_combined
            
        except Exception as e:
            logger.error(f"Error adding numerical features: {e}")
            return X
    
    async def _train_model(self, X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, config: TrainingConfig) -> Tuple[Any, Dict[str, float]]:
        """Train the model and return metrics"""
        try:
            start_time = time.time()
            
            # Select model based on type
            if config.model_type == ModelType.QUALITY_PREDICTOR:
                model = GradientBoostingRegressor(random_state=config.random_state)
            elif config.model_type == ModelType.PRICE_PREDICTOR:
                model = RandomForestRegressor(random_state=config.random_state)
            elif config.model_type == ModelType.CATEGORY_CLASSIFIER:
                from sklearn.ensemble import RandomForestClassifier
                model = RandomForestClassifier(random_state=config.random_state)
            elif config.model_type == ModelType.SIMILITY_SCORER:
                model = LinearRegression()
            else:
                model = LinearRegression()
            
            # Train model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            training_time = time.time() - start_time
            
            if config.model_type in [ModelType.QUALITY_PREDICTOR, ModelType.PRICE_PREDICTOR, ModelType.SIMILITY_SCORER]:
                # Regression metrics
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                metrics = {
                    "rmse": rmse,
                    "mae": mae,
                    "r2_score": r2,
                    "training_time": training_time
                }
            else:
                # Classification metrics
                from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
                
                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, average='weighted')
                recall = recall_score(y_test, y_pred, average='weighted')
                f1 = f1_score(y_test, y_pred, average='weighted')
                
                metrics = {
                    "accuracy": accuracy,
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1,
                    "training_time": training_time
                }
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train, y_train, cv=config.cross_validation_folds)
            metrics["cross_val_score"] = np.mean(cv_scores)
            
            # Feature importance
            if hasattr(model, 'feature_importances_'):
                feature_importance = dict(zip(config.features, model.feature_importances_))
                metrics["feature_importance"] = feature_importance
            
            return model, metrics
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    async def _validate_model(self, model: Any, X_test: np.ndarray, y_test: np.ndarray, config: TrainingConfig) -> Dict[str, float]:
        """Validate the model on test data"""
        try:
            start_time = time.time()
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate validation metrics
            prediction_time = time.time() - start_time
            
            if config.model_type in [ModelType.QUALITY_PREDICTOR, ModelType.PRICE_PREDICTOR, ModelType.SIMILITY_SCORER]:
                # Regression metrics
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                metrics = {
                    "validation_rmse": rmse,
                    "validation_mae": mae,
                    "validation_r2": r2,
                    "prediction_time": prediction_time
                }
            else:
                # Classification metrics
                from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
                
                accuracy = accuracy_score(y_test, y_pred)
                precision = precision_score(y_test, y_pred, average='weighted')
                recall = recall_score(y_test, y_pred, average='weighted')
                f1 = f1_score(y_test, y_pred, average='weighted')
                
                metrics = {
                    "validation_accuracy": accuracy,
                    "validation_precision": precision,
                    "validation_recall": recall,
                    "validation_f1": f1,
                    "prediction_time": prediction_time
                }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error validating model: {e}")
            return {}
    
    async def _save_model(self, model: Any, model_type: ModelType, job_id: str) -> str:
        """Save trained model to disk"""
        try:
            # Create model path
            model_path = f"models/{model_type.value}_{job_id}.pkl"
            
            # Save model
            joblib.dump(model, model_path)
            
            # Save metadata
            metadata = {
                "model_type": model_type.value,
                "job_id": job_id,
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            
            metadata_path = f"models/{model_type.value}_{job_id}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return model_path
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise
    
    async def load_model(self, model_path: str) -> Any:
        """Load a trained model from disk"""
        try:
            model = joblib.load(model_path)
            return model
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    async def predict_quality(self, item_data: Dict[str, Any], model_id: str = None) -> Dict[str, Any]:
        """Predict quality score for an item"""
        try:
            # Use latest model if no specific model ID provided
            if not model_id:
                model_id = self._get_latest_model(ModelType.QUALITY_PREDICTOR)
            
            if not model_id:
                raise Exception("No quality prediction model available")
            
            # Get model
            model = self.models.get(model_id)
            if not model:
                model = await self.load_model(self.training_jobs[model_id].model_path)
                self.models[model_id] = model
            
            # Prepare features
            features = await self._prepare_item_features(item_data, ModelType.QUALITY_PREDICTOR)
            
            # Make prediction
            prediction = model.predict([features])[0]
            
            # Apply quality modifiers
            modified_prediction = await self._apply_quality_modifiers(prediction, item_data)
            
            return {
                "predicted_quality": prediction,
                "modified_quality": modified_prediction,
                "model_id": model_id,
                "confidence": self._calculate_prediction_confidence(features, model)
            }
            
        except Exception as e:
            logger.error(f"Error predicting quality: {e}")
            raise
    
    async def _prepare_item_features(self, item_data: Dict[str, Any], model_type: ModelType) -> List[float]:
        """Prepare features for a single item"""
        try:
            config = self.default_configs.get(model_type)
            if not config:
                raise Exception(f"No configuration found for {model_type.value}")
            
            features = []
            
            for feature_name in config.features:
                if feature_name in item_data:
                    features.append(item_data[feature_name])
                else:
                    features.append(0)
            
            # Add text features
            if config.use_text_features:
                text_features = await self._extract_text_features(item_data)
                features.extend(text_features)
            
            # Add categorical features
            if config.use_categorical_features:
                categorical_features = await self._encode_categorical_features(item_data, model_type)
                features.extend(categorical_features)
            
            # Add numerical features
            if config.use_numerical_features:
                numerical_features = await _extract_numerical_features(item_data)
                features.extend(numerical_features)
            
            # Scale features
            scaler_key = f"{model_type.value}_scaler"
            scaler = self.scalers.get(scaler_key)
            if scaler:
                features = scaler.transform([features])[0]
            
            return features
            
        except Exception as e:
            logger.error(f"Error preparing item features: {e}")
            raise
    
    async def _extract_text_features(self, item_data: Dict[str, Any]) -> List[float]:
        """Extract text features using TF-IDF"""
        try:
            # Combine text fields
            text_parts = []
            
            if item_data.get("title"):
                text_parts.append(item_data["title"])
            
            if item_data.get("description"):
                text_parts.append(item_data["description"])
            
            if item_data.get("keywords"):
                text_parts.extend(item_data["keywords"])
            
            combined_text = " ".join(text_parts)
            
            # Use vectorizer
            vectorizer_key = "quality_predictor_vectorizer"
            vectorizer = self.vectorizers.get(vectorizer_key)
            
            if vectorizer:
                text_features = vectorizer.transform([combined_text])
                return text_features.toarray()[0]
            else:
                return []
            
        except Exception as e:
            logger.error(f"Error extracting text features: {e}")
            return []
    
    async def _encode_categorical_features(self, item_data: Dict[str, Any], model_type: ModelType) -> List[float]:
        """Encode categorical features"""
        try:
            categorical_features = ["category", "brand", "condition", "platform"]
            encoded_values = []
            
            for feature_name in categorical_features:
                encoder_key = f"{model_type.value}_{feature_name}_encoder"
                encoder = self.encoders.get(encoder_key)
                
                if encoder and feature_name in item_data:
                    encoded_value = encoder.transform([item_data[feature_name]])[0]
                    encoded_values.append(encoded_value)
                else:
                    encoded_values.append(0)
            
            return encoded_values
            
        except Exception as e:
            logger.error(f"Error encoding categorical features: {e}")
            return []
    
    def _extract_numerical_features(self, item_data: Dict[str, Any]) -> List[float]:
        """Extract numerical features"""
        try:
            return [
                len(item_data.get("title", "")),
                len(item_data.get("description", "")),
                len(item_data.get("images", [])),
                len(item_data.get("keywords", [])),
                len(item_data.get("features", []))
            ]
        except Exception as e:
            logger.error(f"Error extracting numerical features: {e}")
            return [0, 0, 0, 0, 0]
    
    async def _apply_quality_modifiers(self, predicted_quality: float, item_data: Dict[str, Any]) -> float:
        """Apply quality modifiers to prediction"""
        try:
            modified_quality = predicted_quality
            
            for modifier in self.quality_modifiers.values():
                if not modifier.is_active:
                    continue
                
                # Check if modifier applies to this item
                if await self._modifier_applies(modifier, item_data):
                    # Apply modifier
                    if modifier.modifier_type == "additive":
                        modified_quality += modifier.parameters.get("value", 0)
                    elif modifier.modifier_type == "multiplicative":
                        modified_quality *= modifier.parameters.get("factor", 1.0)
                    elif modifier.modifier_type == "rule_based":
                        modified_quality = await self._apply_rule_based_modifier(modifier, modified_quality, item_data)
                    
                    # Clamp to valid range
                    modified_quality = max(0.0, min(1.0, modified_quality))
            
            return modified_quality
            
        except Exception as e:
            logger.error(f"Error applying quality modifiers: {e}")
            return predicted_quality
    
    async def _modifier_applies(self, modifier: QualityModifier, item_data: Dict[str, Any]) -> bool:
        """Check if a quality modifier applies to an item"""
        try:
            # Check confidence threshold
            if modifier.confidence_threshold > 0:
                # This would require confidence calculation
                pass
            
            # Check category filter
            if "categories" in modifier.parameters:
                if item_data.get("category") not in modifier.parameters["categories"]:
                    return False
            
            # Check brand filter
            if "brands" in modifier.parameters:
                if item_data.get("brand") not in modifier.parameters["brands"]:
                    return False
            
            # Check price range
            if "price_range" in modifier.parameters:
                price = item_data.get("price", 0)
                price_range = modifier.parameters["price_range"]
                if not (price_range[0] <= price <= price_range[1]):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking modifier applicability: {e}")
            return False
    
    async def _apply_rule_based_modifier(self, modifier: QualityModifier, current_quality: float, item_data: Dict[str, Any]) -> float:
        """Apply rule-based quality modifier"""
        try:
            rules = modifier.parameters.get("rules", [])
            
            for rule in rules:
                condition = rule.get("condition")
                action = rule.get("action")
                
                if condition and action:
                    # Evaluate condition
                    if await self._evaluate_rule_condition(condition, item_data):
                        # Apply action
                        if action["type"] == "add":
                            current_quality += action["value"]
                        elif action["type"] == "multiply":
                            current_quality *= action["factor"]
                        elif action["type"] == "set":
                            current_quality = action["value"]
            
            return current_quality
            
        except Exception as e:
            logger.error(f"Error applying rule-based modifier: {e}")
            return current_quality
    
    async def _evaluate_rule_condition(self, condition: Dict[str, Any], item_data: Dict[str, Any]) -> bool:
        """Evaluate a rule condition"""
        try:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")
            
            if not field or operator not in ["equals", "contains", "greater_than", "less_than", "in"]:
                return False
            
            item_value = item_data.get(field)
            
            if operator == "equals":
                return item_value == value
            elif operator == "contains":
                return value in str(item_value)
            elif operator == "greater_than":
                return float(item_value) > float(value)
            elif operator == "less_than":
                return float(item_value) < float(value)
            elif operator == "in":
                return item_value in value
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating rule condition: {e}")
            return False
    
    def _calculate_prediction_confidence(self, features: List[float], model: Any) -> float:
        """Calculate confidence in prediction"""
        try:
            # This is a simplified confidence calculation
            # In practice, you might use methods like prediction variance, ensemble methods, etc.
            if hasattr(model, 'predict_proba'):
                # For classification models
                probabilities = model.predict_proba([features])[0]
                confidence = max(probabilities)
            else:
                # For regression models, use a heuristic based on feature values
                feature_variance = np.var(features)
                confidence = min(1.0, feature_variance / 10.0)  # Normalize variance
            
            return confidence
            
        except Exception as e:
            logger.error(f"Error calculating prediction confidence: {e}")
            return 0.5
    
    def _get_latest_model(self, model_type: ModelType) -> Optional[str]:
        """Get the latest model for a given type"""
        try:
            latest_job = None
            latest_time = None
            
            for job_id, job in self.training_jobs.items():
                if job.model_type == model_type and job.status == TrainingStatus.COMPLETED:
                    if not latest_time or job.completed_at > latest_time:
                        latest_time = job.completed_at
                        latest_job = job_id
            
            return latest_job
            
        except Exception as e:
            logger.error(f"Error getting latest model: {e}")
            return None
    
    async def create_quality_modifier(self, name: str, description: str, modifier_type: str, parameters: Dict[str, Any], user_id: str = None) -> QualityModifier:
        """Create a new quality modifier"""
        try:
            modifier_id = hashlib.md5(f"{name}_{datetime.now().isoformat()}".encode()).hexdigest()
            
            modifier = QualityModifier(
                id=modifier_id,
                name=name,
                description=description,
                model_version="1.0.0",
                modifier_type=modifier_type,
                parameters=parameters,
                confidence_threshold=parameters.get("confidence_threshold", 0.0),
                quality_improvement=parameters.get("quality_improvement", 0.0),
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.quality_modifiers[modifier_id] = modifier
            
            # Store in database
            await self._store_quality_modifier(modifier)
            
            return modifier
            
        except Exception as e:
            logger.error(f"Error creating quality modifier: {e}")
            raise
    
    async def _store_quality_modifier(self, modifier: QualityModifier):
        """Store quality modifier in database"""
        try:
            modifier_data = {
                "id": modifier.id,
                "name": modifier.name,
                "description": modifier.description,
                "model_version": modifier.model_version,
                "modifier_type": modifier.modifier_type,
                "parameters": modifier.parameters,
                "confidence_threshold": modifier.confidence_threshold,
                "quality_improvement": modifier.quality_improvement,
                "is_active": modifier.is_active,
                "created_at": modifier.created_at.isoformat(),
                "updated_at": modifier.updated_at.isoformat()
            }
            
            await self.supabase.from("quality_modifiers").upsert(modifier_data)
            
        except Exception as e:
            logger.error(f"Error storing quality modifier: {e}")
            raise
    
    async def get_training_jobs(self, user_id: str = None, status: TrainingStatus = None) -> List[TrainingJob]:
        """Get training jobs with optional filtering"""
        try:
            jobs = []
            
            for job_id, job in self.training_jobs.items():
                if user_id and job.user_id != user_id:
                    continue
                
                if status and job.status != status:
                    continue
                
                jobs.append(job)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error getting training jobs: {e}")
            return []
    
    async def get_quality_modifiers(self, user_id: str = None, active_only: bool = False) -> List[QualityModifier]:
        """Get quality modifiers with optional filtering"""
        try:
            modifiers = []
            
            for modifier_id, modifier in self.quality_modifiers.items():
                if user_id and modifier.user_id != user_id:
                    continue
                
                if active_only and not modifier.is_active:
                    continue
                
                modifiers.append(modifier)
            
            return modifiers
            
        except Exception as e:
            logger.error(f"Error getting quality modifiers: {e}")
            return []
    
    async def delete_quality_modifier(self, modifier_id: str) -> bool:
        """Delete a quality modifier"""
        try:
            if modifier_id in self.quality_modifiers:
                del self.quality_modifiers[modifier_id]
                
                # Delete from database
                await self.supabase.from("quality_modifiers").delete().eq("id", modifier_id).execute()
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting quality modifier: {e}")
            return False
    
    async def retrain_models(self, model_types: List[ModelType] = None, user_id: str = None) -> List[TrainingJob]:
        """Retrain multiple models"""
        try:
            if not model_types:
                model_types = list(ModelType)
            
            jobs = []
            
            for model_type in model_types:
                job = await self.train_model(model_type, user_id=user_id)
                jobs.append(job)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error retraining models: {e}")
            raise
    
    async def get_model_performance(self, model_type: ModelType, days: int = 30) -> Dict[str, Any]:
        """Get model performance metrics"""
        try:
            # Get training jobs for the model type
            jobs = []
            for job_id, job in self.training_jobs.items():
                if job.model_type == model_type and job.status == TrainingStatus.COMPLETED:
                    # Check if job was completed within the specified days
                    if job.completed_at and (datetime.now() - job.completed_at).days <= days:
                        jobs.append(job)
            
            if not jobs:
                return {}
            
            # Calculate aggregate metrics
            metrics = {
                "total_jobs": len(jobs),
                "average_accuracy": np.mean([job.metrics.accuracy for job in jobs if job.metrics]),
                "average_precision": np.mean([job.metrics.precision for job in jobs if job.metrics]),
                "average_recall": np.mean([job.metrics.recall for job in jobs if job.metrics]),
                "average_f1": np.mean([job.metrics.f1_score for job in jobs if job.metrics]),
                "average_rmse": np.mean([job.metrics.rmse for job in jobs if job.metrics]),
                "average_mae": np.mean([job.metrics.mae for job in jobs if job.metrics]),
                "average_r2": np.mean([job.metrics.r2_score for job in jobs if job.metrics]),
                "average_training_time": np.mean([job.metrics.training_time for job in jobs if job.metrics]),
                "best_job": max(jobs, key=lambda j: j.metrics.accuracy if j.metrics else 0) if jobs else None
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            return {}