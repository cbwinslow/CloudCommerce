
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, AsyncGenerator
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import hashlib
import uuid
from letta import LettaClient
from litellm import completion
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import queue
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSource(Enum):
    EBAY = "ebay"
    AMAZON = "amazon"
    MERCARI = "mercari"
    FACEBOOK_MARKETPLACE = "facebook_marketplace"
    CRAIGSLIST = "craigslist"
    OFFICIAL_API = "official_api"

class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DUPLICATE = "duplicate"
    VALIDATED = "validated"

class DataQuality(Enum):
    POOR = 1
    FAIR = 2
    GOOD = 3
    EXCELLENT = 4
    PERFECT = 5

@dataclass
class RawItem:
    id: str
    source: DataSource
    platform_id: str
    title: str
    description: str
    price: float
    currency: str
    category: str
    condition: str
    brand: str
    model: str
    images: List[str]
    features: List[str]
    keywords: List[str]
    location: str
    seller_info: Dict[str, Any]
    metadata: Dict[str, Any]
    raw_data: Dict[str, Any]
    crawled_at: datetime
    processing_status: ProcessingStatus
    data_quality: DataQuality
    confidence_score: float
    processing_attempts: int = 0
    last_processed: Optional[datetime] = None
    error_message: Optional[str] = None

@dataclass
class ProcessedItem:
    id: str
    source: DataSource
    platform_id: str
    title: str
    description: str
    price: float
    currency: str
    category: str
    condition: str
    brand: str
    model: str
    features: List[str]
    keywords: List[str]
    location: str
    seller_info: Dict[str, Any]
    metadata: Dict[str, Any]
    images: List[str]
    quality_score: float
    confidence_score: float
    estimated_market_value: float
    arbitrage_potential: float
    processing_time: float
    processed_at: datetime
    validated: bool
    validation_score: float
    search_index: Dict[str, Any]  # For similarity search

@dataclass
class IngestionJob:
    id: str
    source: DataSource
    batch_id: str
    items: List[RawItem]
    status: ProcessingStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    processed_count: int = 0
    failed_count: int = 0
    duplicate_count: int = 0
    processing_time: float = 0.0
    error_message: Optional[str] = None

class DataPipeline:
    def __init__(self, supabase_client, letta_client: LettaClient):
        self.supabase = supabase_client
        self.letta = letta_client
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Pipeline components
        self.ingestion_queue = queue.Queue()
        self.processing_queue = queue.Queue()
        self.validation_queue = queue.Queue()
        
        # Configuration
        self.batch_size = 100
        self.max_retries = 3
        self.retry_delay = 60  # seconds
        self.quality_threshold = 0.5
        self.confidence_threshold = 0.7
        
        # Processing workers
        self.workers = []
        self.running = False
        
        # Initialize agent IDs
        self.agent_ids = {
            "processing": os.getenv("LETTA_PROCESSING_AGENT_ID"),
            "validation": os.getenv("LETTA_VALIDATION_AGENT_ID"),
            "quality": os.getenv("LETTA_QUALITY_AGENT_ID"),
            "metadata": os.getenv("LETTA_METADATA_AGENT_ID")
        }
        
        # Data sources configuration
        self.source_configs = {
            DataSource.EBAY: {
                "rate_limit": 1,  # requests per second
                "max_retries": 3,
                "timeout": 30,
                "endpoints": {
                    "search": "https://api.ebay.com/sell/fulfillment/v1/order",
                    "item": "https://api.ebay.com/sell/fulfillment/v1/order/{order_id}"
                }
            },
            DataSource.AMAZON: {
                "rate_limit": 2,
                "max_retries": 3,
                "timeout": 30,
                "endpoints": {
                    "search": "https://api.amazon.com/orders/v0/orders",
                    "item": "https://api.amazon.com/orders/v0/orders/{order_id}"
                }
            },
            DataSource.MERCARI: {
                "rate_limit": 1,
                "max_retries": 3,
                "timeout": 30,
                "endpoints": {
                    "search": "https://api.mercari.com/v1/user/items",
                    "item": "https://api.mercari.com/v1/user/items/{item_id}"
                }
            },
            DataSource.FACEBOOK_MARKETPLACE: {
                "rate_limit": 1,
                "max_retries": 3,
                "timeout": 30,
                "endpoints": {
                    "search": "https://graph.facebook.com/v18.0/me/marketplace_listings",
                    "item": "https://graph.facebook.com/v18.0/marketplace_listing/{item_id}"
                }
            }
        }
    
    async def start_pipeline(self):
        """Start the data processing pipeline"""
        try:
            self.running = True
            
            # Start worker threads
            self.workers = [
                threading.Thread(target=self._ingestion_worker, daemon=True),
                threading.Thread(target=self._processing_worker, daemon=True),
                threading.Thread(target=self._validation_worker, daemon=True),
                threading.Thread(target=self._storage_worker, daemon=True)
            ]
            
            for worker in self.workers:
                worker.start()
            
            logger.info("Data pipeline started")
            
        except Exception as e:
            logger.error(f"Error starting pipeline: {e}")
            raise
    
    async def stop_pipeline(self):
        """Stop the data processing pipeline"""
        try:
            self.running = False
            
            # Wait for workers to finish
            for worker in self.workers:
                worker.join(timeout=5)
            
            logger.info("Data pipeline stopped")
            
        except Exception as e:
            logger.error(f"Error stopping pipeline: {e}")
    
    async def ingest_data(self, source: DataSource, items: List[Dict[str, Any]], batch_id: str = None) -> IngestionJob:
        """Ingest raw data into the pipeline"""
        try:
            if not batch_id:
                batch_id = str(uuid.uuid4())
            
            # Create raw items
            raw_items = []
            for item_data in items:
                raw_item = self._create_raw_item(source, item_data)
                raw_items.append(raw_item)
            
            # Create ingestion job
            job_id = hashlib.md5(f"{source.value}_{batch_id}_{datetime.now().isoformat()}".encode()).hexdigest()
            job = IngestionJob(
                id=job_id,
                source=source,
                batch_id=batch_id,
                items=raw_items,
                status=ProcessingStatus.PENDING,
                created_at=datetime.now()
            )
            
            # Add to ingestion queue
            self.ingestion_queue.put(job)
            
            logger.info(f"Created ingestion job {job_id} with {len(raw_items)} items")
            
            return job
            
        except Exception as e:
            logger.error(f"Error ingesting data: {e}")
            raise
    
    def _create_raw_item(self, source: DataSource, item_data: Dict[str, Any]) -> RawItem:
        """Create a RawItem from raw data"""
        try:
            # Generate unique ID
            item_id = hashlib.md5(f"{source.value}_{item_data.get('id', '')}_{datetime.now().isoformat()}".encode()).hexdigest()
            
            # Extract basic fields
            raw_item = RawItem(
                id=item_id,
                source=source,
                platform_id=item_data.get("id", ""),
                title=item_data.get("title", ""),
                description=item_data.get("description", ""),
                price=float(item_data.get("price", 0)),
                currency=item_data.get("currency", "USD"),
                category=item_data.get("category", ""),
                condition=item_data.get("condition", ""),
                brand=item_data.get("brand", ""),
                model=item_data.get("model", ""),
                images=item_data.get("images", []),
                features=item_data.get("features", []),
                keywords=item_data.get("keywords", []),
                location=item_data.get("location", ""),
                seller_info=item_data.get("seller_info", {}),
                metadata=item_data.get("metadata", {}),
                raw_data=item_data,
                crawled_at=datetime.now(),
                processing_status=ProcessingStatus.PENDING,
                data_quality=DataQuality.FAIR,
                confidence_score=0.5
            )
            
            return raw_item
            
        except Exception as e:
            logger.error(f"Error creating raw item: {e}")
            raise
    
    def _ingestion_worker(self):
        """Worker for ingesting raw data"""
        while self.running:
            try:
                # Get job from queue
                job = self.ingestion_queue.get(timeout=1)
                
                if job:
                    # Process job
                    self._process_ingestion_job(job)
                    
                    # Add to processing queue
                    self.processing_queue.put(job)
                
                self.ingestion_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in ingestion worker: {e}")
    
    def _process_ingestion_job(self, job: IngestionJob):
        """Process an ingestion job"""
        try:
            job.status = ProcessingStatus.PROCESSING
            job.started_at = datetime.now()
            
            # Process each item
            for raw_item in job.items:
                try:
                    # Validate item
                    if self._validate_raw_item(raw_item):
                        # Process item
                        processed_item = self._process_raw_item(raw_item)
                        
                        # Add to validation queue
                        self.validation_queue.put((job, processed_item))
                        
                        job.processed_count += 1
                    else:
                        job.failed_count += 1
                        raw_item.processing_status = ProcessingStatus.FAILED
                        raw_item.error_message = "Validation failed"
                        
                except Exception as e:
                    logger.error(f"Error processing item {raw_item.id}: {e}")
                    job.failed_count += 1
                    raw_item.processing_status = ProcessingStatus.FAILED
                    raw_item.error_message = str(e)
            
            job.status = ProcessingStatus.COMPLETED
            job.completed_at = datetime.now()
            job.processing_time = (job.completed_at - job.started_at).total_seconds()
            
        except Exception as e:
            logger.error(f"Error processing ingestion job {job.id}: {e}")
            job.status = ProcessingStatus.FAILED
            job.error_message = str(e)
    
    def _validate_raw_item(self, raw_item: RawItem) -> bool:
        """Validate a raw item"""
        try:
            # Check required fields
            if not raw_item.title or not raw_item.description:
                return False
            
            # Check price
            if raw_item.price <= 0:
                return False
            
            # Check data quality
            if len(raw_item.title) < 10:
                return False
            
            if len(raw_item.description) < 20:
                return False
            
            # Check for duplicates
            if self._is_duplicate(raw_item):
                raw_item.processing_status = ProcessingStatus.DUPLICATE
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating raw item {raw_item.id}: {e}")
            return False
    
    def _is_duplicate(self, raw_item: RawItem) -> bool:
        """Check if item is a duplicate"""
        try:
            # Check database for duplicates
            response = self.supabase.from("crawled_items").select("id").eq("platform_id", raw_item.platform_id).eq("source", raw_item.source.value).execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            return False
    
    def _process_raw_item(self, raw_item: RawItem) -> ProcessedItem:
        """Process a raw item into a processed item"""
        try:
            start_time = time.time()
            
            # Extract and enhance metadata
            enhanced_metadata = self._extract_enhanced_metadata(raw_item)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(raw_item, enhanced_metadata)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(raw_item, enhanced_metadata)
            
            # Estimate market value
            estimated_market_value = self._estimate_market_value(raw_item, enhanced_metadata)
            
            # Calculate arbitrage potential
            arbitrage_potential = self._calculate_arbitrage_potential(raw_item, enhanced_metadata)
            
            # Create search index
            search_index = self._create_search_index(raw_item, enhanced_metadata)
            
            # Create processed item
            processed_item = ProcessedItem(
                id=raw_item.id,
                source=raw_item.source,
                platform_id=raw_item.platform_id,
                title=enhanced_metadata.get("title", raw_item.title),
                description=enhanced_metadata.get("description", raw_item.description),
                price=raw_item.price,
                currency=raw_item.currency,
                category=enhanced_metadata.get("category", raw_item.category),
                condition=enhanced_metadata.get("condition", raw_item.condition),
                brand=enhanced_metadata.get("brand", raw_item.brand),
                model=enhanced_metadata.get("model", raw_item.model),
                features=enhanced_metadata.get("features", raw_item.features),
                keywords=enhanced_metadata.get("keywords", raw_item.keywords),
                location=raw_item.location,
                seller_info=raw_item.seller_info,
                metadata=enhanced_metadata,
                images=raw_item.images,
                quality_score=quality_score,
                confidence_score=confidence_score,
                estimated_market_value=estimated_market_value,
                arbitrage_potential=arbitrage_potential,
                processing_time=time.time() - start_time,
                processed_at=datetime.now(),
                validated=False,
                validation_score=0.0,
                search_index=search_index
            )
            
            return processed_item
            
        except Exception as e:
            logger.error(f"Error processing raw item {raw_item.id}: {e}")
            raise
    
    def _extract_enhanced_metadata(self, raw_item: RawItem) -> Dict[str, Any]:
        """Extract enhanced metadata from raw item"""
        try:
            # Use Letta agent for metadata extraction
            agent_id = self.agent_ids["metadata"]
            agent = self.letta.agents.get(agent_id)
            
            # Prepare prompt
            prompt = f"""
            Extract and enhance metadata from this item:
            
            Title: {raw_item.title}
            Description: {raw_item.description}
            Category: {raw_item.category}
            Condition: {raw_item.condition}
            Brand: {raw_item.brand}
            Model: {raw_item.model}
            Features: {', '.join(raw_item.features)}
            Keywords: {', '.join(raw_item.keywords)}
            Price: ${raw_item.price}
            
            Return JSON with enhanced metadata including:
            - enhanced_title: More descriptive title
            - enhanced_description: Enhanced description
            - category: Specific category
            - condition: Detailed condition
            - brand: Identified brand
            - model: Identified model
            - features: Enhanced features list
            - keywords: Enhanced keywords list
            - target_audience: Target audience
            - seasonality: Seasonal relevance
            - estimated_market_value: Market value estimate
            """
            
            # Get AI response
            response = agent.messages.create(content=prompt, role="user")
            
            # Parse response
            try:
                enhanced_metadata = json.loads(response.content)
                return enhanced_metadata
            except json.JSONDecodeError:
                logger.error("Failed to parse metadata extraction response")
                return {}
            
        except Exception as e:
            logger.error(f"Error extracting enhanced metadata: {e}")
            return {}
    
    def _calculate_quality_score(self, raw_item: RawItem, enhanced_metadata: Dict[str, Any]) -> float:
        """Calculate quality score for item"""
        try:
            factors = []
            
            # Title quality
            title_length = len(raw_item.title)
            if title_length >= 50:
                factors.append(1.0)
            elif title_length >= 30:
                factors.append(0.7)
            else:
                factors.append(0.3)
            
            # Description quality
            desc_length = len(raw_item.description)
            if desc_length >= 200:
                factors.append(1.0)
            elif desc_length >= 100:
                factors.append(0.7)
            else:
                factors.append(0.3)
            
            # Image quality
            image_count = len(raw_item.images)
            if image_count >= 5:
                factors.append(1.0)
            elif image_count >= 3:
                factors.append(0.7)
            elif image_count >= 1:
                factors.append(0.5)
            else:
                factors.append(0.0)
            
            # Metadata completeness
            metadata_fields = ["brand", "model", "category", "condition"]
            completed_fields = sum(1 for field in metadata_fields if enhanced_metadata.get(field))
            factors.append(completed_fields / len(metadata_fields))
            
            # Price reasonableness
            if raw_item.price > 0:
                factors.append(0.8)  # Basic price validation
            else:
                factors.append(0.0)
            
            # Calculate weighted average
            weights = [0.2, 0.3, 0.2, 0.2, 0.1]
            quality_score = sum(f * w for f, w in zip(factors, weights))
            
            return round(quality_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.0
    
    def _calculate_confidence_score(self, raw_item: RawItem, enhanced_metadata: Dict[str, Any]) -> float:
        """Calculate confidence score for item"""
        try:
            # Use Letta agent for confidence calculation
            agent_id = self.agent_ids["quality"]
            agent = self.letta.agents.get(agent_id)
            
            prompt = f"""
            Calculate confidence score for this item's metadata:
            
            Title: {raw_item.title}
            Description: {raw_item.description}
            Enhanced Metadata: {json.dumps(enhanced_metadata, indent=2)}
            
            Provide a confidence score (0.0 to 1.0) based on:
            - Data completeness
            - Information accuracy
            - Consistency across fields
            - Source reliability
            
            Return only the score as a number.
            """
            
            response = agent.messages.create(content=prompt, role="user")
            
            try:
                confidence_score = float(response.content.strip())
                return min(1.0, max(0.0, confidence_score))
            except ValueError:
                return 0.5
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5
    
    def _estimate_market_value(self, raw_item: RawItem, enhanced_metadata: Dict[str, Any]) -> float:
        """Estimate market value for item"""
        try:
            # Use Letta agent for market value estimation
            agent_id = self.agent_ids["quality"]
            agent = self.letta.agents.get(agent_id)
            
            prompt = f"""
            Estimate market value for this item:
            
            Title: {raw_item.title}
            Description: {raw_item.description}
            Category: {enhanced_metadata.get('category', '')}
            Condition: {enhanced_metadata.get('condition', '')}
            Brand: {enhanced_metadata.get('brand', '')}
            Model: {enhanced_metadata.get('model', '')}
            Features: {', '.join(enhanced_metadata.get('features', []))}
            Current Price: ${raw_item.price}
            
            Consider:
            - Item condition
            - Brand reputation
            - Market demand
            - Seasonal factors
            - Comparable items
            
            Return estimated market value as a number.
            """
            
            response = agent.messages.create(content=prompt, role="user")
            
            try:
                estimated_value = float(response.content.strip())
                return max(0, estimated_value)
            except ValueError:
                return raw_item.price
            
        except Exception as e:
            logger.error(f"Error estimating market value: {e}")
            return raw_item.price
    
    def _calculate_arbitrage_potential(self, raw_item: RawItem, enhanced_metadata: Dict[str, Any]) -> float:
        """Calculate arbitrage potential for item"""
        try:
            # Get similar items from database
            similar_items = self._get_similar_items(raw_item)
            
            if not similar_items:
                return 0.0
            
            # Calculate average price
            avg_price = sum(item["price"] for item in similar_items) / len(similar_items)
            
            # Calculate arbitrage potential
            if raw_item.price < avg_price * 0.7:
                arbitrage_potential = (avg_price - raw_item.price) / avg_price
            else:
                arbitrage_potential = 0.0
            
            return round(arbitrage_potential, 2)
            
        except Exception as e:
            logger.error(f"Error calculating arbitrage potential: {e}")
            return 0.0
    
    def _get_similar_items(self, raw_item: RawItem) -> List[Dict[str, Any]]:
        """Get similar items from database"""
        try:
            response = self.supabase.from("search_index").select("price").eq("category", raw_item.category).eq("brand", raw_item.brand).limit(10).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting similar items: {e}")
            return []
    
    def _create_search_index(self, raw_item: RawItem, enhanced_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create search index for similarity search"""
        try:
            # Combine all searchable text
            searchable_text = []
            
            searchable_text.append(raw_item.title.lower())
            searchable_text.append(raw_item.description.lower())
            
            if enhanced_metadata.get("brand"):
                searchable_text.append(enhanced_metadata["brand"].lower())
            
            if enhanced_metadata.get("model"):
                searchable_text.append(enhanced_metadata["model"].lower())
            
            if enhanced_metadata.get("category"):
                searchable_text.append(enhanced_metadata["category"].lower())
            
            searchable_text.extend([kw.lower() for kw in enhanced_metadata.get("keywords", [])])
            searchable_text.extend([feat.lower() for feat in enhanced_metadata.get("features", [])])
            
            # Create search index
            search_index = {
                "text": " ".join(searchable_text),
                "title_tokens": raw_item.title.lower().split(),
                "description_tokens": raw_item.description.lower().split(),
                "category": enhanced_metadata.get("category", "").lower(),
                "brand": enhanced_metadata.get("brand", "").lower(),
                "model": enhanced_metadata.get("model", "").lower(),
                "keywords": enhanced_metadata.get("keywords", []),
                "features": enhanced_metadata.get("features", []),
                "price_range": self._get_price_range(raw_item.price),
                "condition": enhanced_metadata.get("condition", "").lower()
            }
            
            return search_index
            
        except Exception as e:
            logger.error(f"Error creating search index: {e}")
            return {}
    
    def _get_price_range(self, price: float) -> str:
        """Get price range category"""
        if price < 10:
            return "under_10"
        elif price < 50:
            return "10_50"
        elif price < 100:
            return "50_100"
        elif price < 500:
            return "100_500"
        elif price < 1000:
            return "500_1000"
        else:
            return "over_1000"
    
    def _processing_worker(self):
        """Worker for processing items"""
        while self.running:
            try:
                # Get job from queue
                job = self.processing_queue.get(timeout=1)
                
                if job:
                    # Process job (already done in ingestion worker)
                    # This worker is for additional processing if needed
                    pass
                
                self.processing_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in processing worker: {e}")
    
    def _validation_worker(self):
        """Worker for validating processed items"""
        while self.running:
            try:
                # Get item from queue
                job, processed_item = self.validation_queue.get(timeout=1)
                
                if processed_item:
                    # Validate item
                    validation_result = self._validate_processed_item(processed_item)
                    
                    # Update validation status
                    processed_item.validated = validation_result["valid"]
                    processed_item.validation_score = validation_result["score"]
                    
                    # Add to storage queue
                    self.storage_queue.put((job, processed_item))
                
                self.validation_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in validation worker: {e}")
    
    def _validate_processed_item(self, processed_item: ProcessedItem) -> Dict[str, Any]:
        """Validate a processed item"""
        try:
            # Use Letta agent for validation
            agent_id = self.agent_ids["validation"]
            agent = self.letta.agents.get(agent_id)
            
            prompt = f"""
            Validate this processed item:
            
            Title: {processed_item.title}
            Description: {processed_item.description}
            Category: {processed_item.category}
            Condition: {processed_item.condition}
            Brand: {processed_item.brand}
            Model: {processed_item.model}
            Price: ${processed_item.price}
            Quality Score: {processed_item.quality_score}
            Confidence Score: {processed_item.confidence_score}
            
            Check for:
            - Accuracy of information