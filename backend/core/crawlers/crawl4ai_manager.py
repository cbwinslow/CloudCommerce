
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from letta import LettaClient
from litellm import completion
import hashlib
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Platform(Enum):
    EBAY = "ebay"
    AMAZON = "amazon"
    MERCARI = "mercari"
    FACEBOOK_MARKETPLACE = "facebook_marketplace"

@dataclass
class CrawledItem:
    id: str
    platform: Platform
    title: str
    description: str
    price: float
    currency: str
    condition: str
    category: str
    images: List[str]
    seller_info: Dict[str, Any]
    location: str
    listing_url: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    quality_score: float = 0.0
    confidence_score: float = 0.0

@dataclass
class CrawlConfig:
    platform: Platform
    search_queries: List[str]
    max_items: int = 100
    update_interval: int = 3600  # 1 hour
    enabled: bool = True
    last_crawled: Optional[datetime] = None

class Crawl4AIManager:
    def __init__(self, supabase_client, letta_client: LettaClient):
        self.supabase = supabase_client
        self.letta = letta_client
        self.crawl_configs: Dict[Platform, CrawlConfig] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_running = False
        
        # Initialize crawl configs
        self._initialize_configs()
        
    def _initialize_configs(self):
        """Initialize default crawl configurations for each platform"""
        default_configs = {
            Platform.EBAY: CrawlConfig(
                platform=Platform.EBAY,
                search_queries=["electronics", "clothing", "collectibles"],
                max_items=50,
                update_interval=1800  # 30 minutes
            ),
            Platform.AMAZON: CrawlConfig(
                platform=Platform.AMAZON,
                search_queries=["electronics", "home", "books"],
                max_items=50,
                update_interval=3600  # 1 hour
            ),
            Platform.MERCARI: CrawlConfig(
                platform=Platform.MERCARI,
                search_queries=["electronics", "fashion", "home"],
                max_items=30,
                update_interval=7200  # 2 hours
            ),
            Platform.FACEBOOK_MARKETPLACE: CrawlConfig(
                platform=Platform.FACEBOOK_MARKETPLACE,
                search_queries=["electronics", "furniture", "clothing"],
                max_items=30,
                update_interval=3600  # 1 hour
            )
        }
        
        self.crawl_configs = default_configs
    
    async def start_crawling(self):
        """Start the continuous crawling process"""
        if self.is_running:
            logger.warning("Crawling is already running")
            return
            
        self.is_running = True
        self.session = aiohttp.ClientSession()
        
        logger.info("Starting continuous crawling process")
        
        while self.is_running:
            try:
                await self._crawl_all_platforms()
                await asyncio.sleep(300)  # Wait 5 minutes between cycles
            except Exception as e:
                logger.error(f"Error in crawling cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def stop_crawling(self):
        """Stop the crawling process"""
        self.is_running = False
        if self.session:
            await self.session.close()
        logger.info("Stopped crawling process")
    
    async def _crawl_all_platforms(self):
        """Crawl all enabled platforms"""
        tasks = []
        
        for platform, config in self.crawl_configs.items():
            if config.enabled and self._should_crawl(config):
                tasks.append(self._crawl_platform(platform, config))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def _should_crawl(self, config: CrawlConfig) -> bool:
        """Check if a platform should be crawled based on update interval"""
        if not config.last_crawled:
            return True
        
        time_since_last_crawl = datetime.now() - config.last_crawled
        return time_since_last_crawl.total_seconds() >= config.update_interval
    
    async def _crawl_platform(self, platform: Platform, config: CrawlConfig):
        """Crawl a specific platform"""
        logger.info(f"Crawling {platform.value} with {len(config.search_queries)} queries")
        
        try:
            all_items = []
            
            for query in config.search_queries:
                items = await self._crawl_platform_query(platform, query)
                all_items.extend(items[:config.max_items // len(config.search_queries)])
            
            # Process and store items
            await self._process_crawled_items(all_items, platform)
            
            # Update last crawled time
            config.last_crawled = datetime.now()
            
            logger.info(f"Successfully crawled {len(all_items)} items from {platform.value}")
            
        except Exception as e:
            logger.error(f"Error crawling {platform.value}: {e}")
    
    async def _crawl_platform_query(self, platform: Platform, query: str) -> List[CrawledItem]:
        """Crawl a specific platform with a search query"""
        try:
            # Use Crawl4AI API to crawl the platform
            crawl_data = await self._call_crawl4ai_api(platform, query)
            
            # Parse and structure the data
            items = await self._parse_crawl_data(crawl_data, platform, query)
            
            return items
            
        except Exception as e:
            logger.error(f"Error crawling {platform.value} with query '{query}': {e}")
            return []
    
    async def _call_crawl4ai_api(self, platform: Platform, query: str) -> Dict[str, Any]:
        """Call Crawl4AI API to crawl the platform"""
        # This is a placeholder implementation
        # In a real implementation, you would call the actual Crawl4AI API
        
        # Simulate API call with mock data
        await asyncio.sleep(1)  # Simulate network delay
        
        mock_data = {
            "platform": platform.value,
            "query": query,
            "items": [
                {
                    "title": f"Sample {query} item on {platform.value}",
                    "price": 29.99,
                    "url": f"https://{platform.value}.com/item/123",
                    "image": "https://example.com/image.jpg",
                    "description": f"Description of {query} item",
                    "seller": {
                        "name": "Sample Seller",
                        "rating": 4.5
                    }
                }
            ]
        }
        
        return mock_data
    
    async def _parse_crawl_data(self, crawl_data: Dict[str, Any], platform: Platform, query: str) -> List[CrawledItem]:
        """Parse crawl data into CrawledItem objects"""
        items = []
        
        for raw_item in crawl_data.get("items", []):
            try:
                item = CrawledItem(
                    id=hashlib.md5(f"{platform.value}_{raw_item['url']}_{datetime.now().isoformat()}".encode()).hexdigest(),
                    platform=platform,
                    title=raw_item.get("title", ""),
                    description=raw_item.get("description", ""),
                    price=float(raw_item.get("price", 0)),
                    currency="USD",
                    condition=self._extract_condition(raw_item),
                    category=query,
                    images=[raw_item.get("image", "")],
                    seller_info=raw_item.get("seller", {}),
                    location=raw_item.get("location", "Unknown"),
                    listing_url=raw_item.get("url", ""),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    metadata={
                        "raw_data": raw_item,
                        "crawl_timestamp": datetime.now().isoformat(),
                        "search_query": query
                    }
                )
                
                items.append(item)
                
            except Exception as e:
                logger.error(f"Error parsing item: {e}")
                continue
        
        return items
    
    def _extract_condition(self, raw_item: Dict[str, Any]) -> str:
        """Extract condition from raw item data"""
        # This would be platform-specific logic
        condition = raw_item.get("condition", "").lower()
        
        if "new" in condition:
            return "new"
        elif "used" in condition:
            return "used"
        elif "refurbished" in condition:
            return "refurbished"
        else:
            return "unknown"
    
    async def _process_crawled_items(self, items: List[CrawledItem], platform: Platform):
        """Process crawled items and store them in the database"""
        if not items:
            return
        
        # Use AI to enhance metadata and quality assessment
        enhanced_items = await self._enhance_items_with_ai(items)
        
        # Store items in database
        await self._store_items(enhanced_items)
        
        # Update search index for similarity matching
        await self._update_search_index(enhanced_items)
    
    async def _enhance_items_with_ai(self, items: List[CrawledItem]) -> List[CrawledItem]:
        """Use AI to enhance item metadata and assess quality"""
        enhanced_items = []
        
        for item in items:
            try:
                # Generate enhanced metadata using AI
                enhanced_metadata = await self._generate_enhanced_metadata(item)
                
                # Calculate quality score
                quality_score = await self._calculate_quality_score(item, enhanced_metadata)
                
                # Calculate confidence score
                confidence_score = await self._calculate_confidence_score(item)
                
                # Update item with AI enhancements
                item.metadata.update(enhanced_metadata)
                item.quality_score = quality_score
                item.confidence_score = confidence_score
                
                enhanced_items.append(item)
                
            except Exception as e:
                logger.error(f"Error enhancing item {item.id}: {e}")
                enhanced_items.append(item)  # Keep original item if enhancement fails
        
        return enhanced_items
    
    async def _generate_enhanced_metadata(self, item: CrawledItem) -> Dict[str, Any]:
        """Generate enhanced metadata using AI"""
        try:
            # Use Letta agent for metadata generation
            agent_id = os.getenv("LETTA_METADATA_AGENT_ID")
            agent = self.letta.agents.get(agent_id)
            
            # Create prompt for metadata generation
            prompt = f"""
            Analyze this item and generate enhanced metadata:
            
            Title: {item.title}
            Description: {item.description}
            Category: {item.category}
            Platform: {item.platform.value}
            Price: ${item.price}
            
            Generate JSON with:
            - enhanced_title: More descriptive title
            - keywords: Relevant keywords for search
            - brand: Brand name (if identifiable)
            - model: Model number (if applicable)
            - features: List of key features
            - specifications: Detailed specifications
            - target_audience: Who this item is for
            - seasonality: Seasonal relevance
            - condition_details: Detailed condition assessment
            - estimated_market_value: Market value estimate
            """
            
            # Get AI response
            response = await agent.messages.create(content=prompt, role="user")
            
            # Parse response as JSON
            enhanced_metadata = json.loads(response.content)
            
            return enhanced_metadata
            
        except Exception as e:
            logger.error(f"Error generating enhanced metadata: {e}")
            return {}
    
    async def _calculate_quality_score(self, item: CrawledItem, enhanced_metadata: Dict[str, Any]) -> float:
        """Calculate quality score for an item"""
        try:
            factors = []
            
            # Title quality
            title_quality = len(item.title) / 100  # Longer titles generally better
            factors.append(min(title_quality, 1.0))
            
            # Description quality
            desc_quality = len(item.description) / 500  # Longer descriptions better
            factors.append(min(desc_quality, 1.0))
            
            # Image quality (would need actual image analysis)
            image_quality = len(item.images) * 0.2  # More images better
            factors.append(min(image_quality, 1.0))
            
            # Price reasonableness
            price_factor = 1.0 if 10 <= item.price <= 1000 else 0.5
            factors.append(price_factor)
            
            # Enhanced metadata completeness
            metadata_completeness = len(enhanced_metadata) / 10  # More metadata better
            factors.append(min(metadata_completeness, 1.0))
            
            # Platform-specific factors
            platform_factor = self._get_platform_quality_factor(item.platform)
            factors.append(platform_factor)
            
            # Calculate weighted average
            quality_score = sum(factors) / len(factors)
            
            return round(quality_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.0
    
    def _get_platform_quality_factor(self, platform: Platform) -> float:
        """Get platform-specific quality factor"""
        quality_factors = {
            Platform.EBAY: 0.9,
            Platform.AMAZON: 0.95,
            Platform.MERCARI: 0.8,
            Platform.FACEBOOK_MARKETPLACE: 0.7
        }
        return quality_factors.get(platform, 0.8)
    
    async def _calculate_confidence_score(self, item: CrawledItem) -> float:
        """Calculate confidence score for item data accuracy"""
        try:
            factors = []
            
            # Data completeness
            completeness = 0.0
            if item.title: completeness += 0.2
            if item.description: completeness += 0.2
            if item.price > 0: completeness += 0.2
            if item.images: completeness += 0.2
            if item.seller_info: completeness += 0.2
            factors.append(completeness)
            
            # Data consistency
            consistency = 1.0  # Would need actual consistency checks
            factors.append(consistency)
            
            # Source reliability
            source_reliability = self._get_source_reliability(item.platform)
            factors.append(source_reliability)
            
            # Calculate average
            confidence_score = sum(factors) / len(factors)
            
            return round(confidence_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.0
    
    def _get_source_reliability(self, platform: Platform) -> float:
        """Get source reliability factor"""
        reliability_factors = {
            Platform.EBAY: 0.9,
            Platform.AMAZON: 0.95,
            Platform.MERCARI: 0.85,
            Platform.FACEBOOK_MARKETPLACE: 0.7
        }
        return reliability_factors.get(platform, 0.8)
    
    async def _store_items(self, items: List[CrawledItem]):
        """Store items in the database"""
        try:
            # Convert items to database format
            items_data = []
            for item in items:
                item_data = {
                    "id": item.id,
                    "platform": item.platform.value,
                    "title": item.title,
                    "description": item.description,
                    "price": item.price,
                    "currency": item.currency,
                    "condition": item.condition,
                    "category": item.category,
                    "images": item.images,
                    "seller_info": item.seller_info,
                    "location": item.location,
                    "listing_url": item.listing_url,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                    "metadata": item.metadata,
                    "quality_score": item.quality_score,
                    "confidence_score": item.confidence_score
                }
                items_data.append(item_data)
            
            # Batch insert into database
            if items_data:
                # Use Supabase upsert to avoid duplicates
                for item_data in items_data:
                    await self.supabase.from("crawled_items").upsert(item_data)
                
                logger.info(f"Stored {len(items_data)} items in database")
                
        except Exception as e:
            logger.error(f"Error storing items: {e}")
    
    async def _update_search_index(self, items: List[CrawledItem]):
        """Update search index for similarity matching"""
        try:
            # This would integrate with a search engine like Elasticsearch
            # For now, we'll store the data in a way that can be searched
            
            search_data = []
            for item in items:
                search_entry = {
                    "item_id": item.id,
                    "platform": item.platform.value,
                    "title": item.title,
                    "description": item.description,
                    "category": item.category,
                    "keywords": item.metadata.get("keywords", []),
                    "brand": item.metadata.get("brand", ""),
                    "model": item.metadata.get("model", ""),
                    "features": item.metadata.get("features", []),
                    "price": item.price,
                    "quality_score": item.quality_score,
                    "confidence_score": item.confidence_score
                }
                search_data.append(search_entry)
            
            # Store search data
            if search_data:
                await self.supabase.from("search_index").insert(search_data)
                logger.info(f"Updated search index with {len(search_data)} items")
                
        except Exception as e:
            logger.error(f"Error updating search index: {e}")
    
    async def find_similar_items(self, target_item: CrawledItem, limit: int = 10) -> List[CrawledItem]:
        """Find similar items using AI-powered similarity search"""
        try:
            # Use AI to generate search query based on target item
            search_query = await self._generate_similarity_query(target_item)
            
            # Search database for similar items
            similar_items = await self._search_similar_items(search_query, target_item, limit)
            
            return similar_items
            
        except Exception as e:
            logger.error(f"Error finding similar items: {e}")
            return []
    
    async def _generate_similarity_query(self, item: CrawledItem) -> str:
        """Generate similarity search query using AI"""
        try:
            # Use Letta agent to generate similarity query
            agent_id = os.getenv("LETTA_SIMILARITY_AGENT_ID")
            agent = self.letta.agents.get(agent_id)
            
            prompt = f"""
            Generate a search query to find similar items for:
            
            Title: {item.title}
            Description: {item.description}
            Category: {item.category}
            Brand: {item.metadata.get('brand', 'Unknown')}
            Model: {item.metadata.get('model', 'Unknown')}
            
            Return a concise search query string.
            """
            
            response = await agent.messages.create(content=prompt, role="user")
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating similarity query: {e}")
            return item.title
    
    async def _search_similar_items(self, search_query: str, target_item: CrawledItem, limit: int) -> List[CrawledItem]:
        """Search database for similar items"""
        try:
            # Use Supabase to search for similar items
            # This is a simplified search - in production you'd use a proper search engine
            
            response = await self.supabase.from("search_index").select("*").text_search(
                "title,description,keywords", search_query
            ).limit(limit).execute()
            
            # Convert search results back to CrawledItem objects
            similar_items = []
            for result in response.data:
                item = CrawledItem(
                    id=result["item_id"],
                    platform=Platform(result["platform"]),
                    title=result["title"],
                    description=result["description"],
                    price=result["price"],
                    currency="USD",
                    condition="unknown",
                    category=result["category"],
                    images=[],
                    seller_info={},
                    location="Unknown",
                    listing_url="",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    metadata={},
                    quality_score=result.get("quality_score", 0.0),
                    confidence_score=result.get("confidence_score", 0.0)
                )
                similar_items.append(item)
            
            return similar_items
            
        except Exception as e:
            logger.error(f"Error searching similar items: {e}")
            return []
    
    async def auto_fill_metadata(self, target_item: CrawledItem) -> Dict[str, Any]:
        """Auto-fill metadata from similar items if confident"""
        try:
            # Find similar items
            similar_items = await self.find_similar_items(target_item, limit=5)
            
            if not similar_items:
                return {}
            
            # Calculate confidence in auto-fill
            avg_confidence = sum(item.confidence_score for item in similar_items) / len(similar_items)
            
            if avg_confidence < 0.7:
                logger.warning(f"Low confidence ({avg_confidence:.2f}) in auto-fill metadata")
                return {}
            
            # Use AI to merge metadata from similar items
            merged_metadata = await self._merge_similar_metadata(target_item, similar_items)
            
            return merged_metadata
            
        except Exception as e:
            logger.error(f"Error auto-filling metadata: {e}")
            return {}
    
    async def _merge_similar_metadata(self, target_item: CrawledItem, similar_items: List[CrawledItem]) -> Dict[str, Any]:
        """Merge metadata from similar items"""
        try:
            # Use Letta agent to merge metadata
            agent_id = os.getenv("LETTA_MERGE_AGENT_ID")
            agent = self.letta.agents.get(agent_id)
            
            # Collect metadata from similar items
            similar_metadata = []
            for item in similar_items:
                if item.metadata:
                    similar_metadata.append(item.metadata)
            
            prompt = f"""
            Merge the following metadata from similar items to fill in missing information for:
            
            Target Item:
            Title: {target_item.title}
            Description: {target_item.description}
            Current Metadata: {target_item.metadata}
            
            Similar Items Metadata:
            {json.dumps(similar_metadata, indent=2)}
            
            Return JSON with merged metadata, filling in missing information from similar items.
            Only include information you're confident about.
            """
            
            response = await agent.messages.create(content=prompt, role="user")
            merged_metadata = json.loads(response.content)
            
            return merged_metadata
            
        except Exception as