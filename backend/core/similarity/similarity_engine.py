
import asyncio
import json
import logging
import math
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from letta import LettaClient
from litellm import completion
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimilarityType(Enum):
    TITLE = "title"
    DESCRIPTION = "description"
    CATEGORY = "category"
    FEATURES = "features"
    KEYWORDS = "keywords"
    OVERALL = "overall"

@dataclass
class SimilarityScore:
    item_id: str
    similarity_type: SimilarityType
    score: float
    matched_fields: List[str]
    confidence: float
    source: str  # "ai", "vector", "keyword", "hybrid"

@dataclass
class SimilarItem:
    item_id: str
    platform: str
    title: str
    description: str
    category: str
    price: float
    condition: str
    brand: str
    model: str
    features: List[str]
    keywords: List[str]
    similarity_scores: List[SimilarityScore]
    overall_similarity: float
    metadata_completeness: float
    quality_score: float
    confidence_score: float
    distance_score: float  # For geographic proximity if applicable
    time_relevance: float  # How recent the item is
    arbitrage_potential: float  # Price difference potential

@dataclass
class SimilarityQuery:
    target_item: Dict[str, Any]
    min_similarity: float = 0.3
    max_results: int = 10
    search_radius: int = 50  # Geographic radius in miles
    price_range: Tuple[float, float] = (0, float('inf'))
    time_window: int = 30  # Days
    platforms: List[str] = None
    categories: List[str] = None
    min_quality_score: float = 0.5
    use_ai_enhancement: bool = True
    use_vector_search: bool = True
    use_keyword_search: bool = True

class SimilarityEngine:
    def __init__(self, supabase_client, letta_client: LettaClient):
        self.supabase = supabase_client
        self.letta = letta_client
        self.session: Optional[aiohttp.ClientSession] = None
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.8
        )
        self.fitted_vectorizer = False
        self.embeddings_cache: Dict[str, np.ndarray] = {}
        self.similarity_cache: Dict[str, List[SimilarItem]] = {}
        self.cache_ttl = 3600  # 1 hour
        
        # Initialize agent IDs
        self.agent_ids = {
            "similarity": os.getenv("LETTA_SIMILARITY_AGENT_ID"),
            "metadata": os.getenv("LETTA_METADATA_AGENT_ID"),
            "merge": os.getenv("LETTA_MERGE_AGENT_ID")
        }
    
    async def find_similar_items(self, query: SimilarityQuery) -> List[SimilarItem]:
        """Find similar items based on the query"""
        try:
            # Check cache first
            cache_key = self._generate_cache_key(query)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info(f"Returning cached result for query: {cache_key}")
                return cached_result
            
            # Start timing
            start_time = datetime.now()
            
            # Get candidate items from database
            candidate_items = await self._get_candidate_items(query)
            
            if not candidate_items:
                logger.warning("No candidate items found")
                return []
            
            # Calculate similarity scores
            similar_items = await self._calculate_similarities(query.target_item, candidate_items, query)
            
            # Filter and rank results
            filtered_items = self._filter_and_rank_items(similar_items, query)
            
            # Cache the result
            self._cache_result(cache_key, filtered_items)
            
            # Log performance
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Found {len(filtered_items)} similar items in {processing_time:.2f}s")
            
            return filtered_items
            
        except Exception as e:
            logger.error(f"Error finding similar items: {e}")
            return []
    
    async def _get_candidate_items(self, query: SimilarityQuery) -> List[Dict[str, Any]]:
        """Get candidate items from database based on query filters"""
        try:
            # Build database query
            db_query = self.supabase.from("search_index").select("*")
            
            # Apply platform filter
            if query.platforms:
                db_query = db_query.in_("platform", query.platforms)
            
            # Apply category filter
            if query.categories:
                db_query = db_query.in_("category", query.categories)
            
            # Apply price range filter
            if query.price_range[1] != float('inf'):
                db_query = db_query.lte("price", query.price_range[1])
            if query.price_range[0] > 0:
                db_query = db_query.gte("price", query.price_range[0])
            
            # Apply quality filter
            if query.min_quality_score > 0:
                db_query = db_query.gte("quality_score", query.min_quality_score)
            
            # Apply time window filter
            if query.time_window > 0:
                cutoff_date = datetime.now() - timedelta(days=query.time_window)
                db_query = db_query.gte("created_at", cutoff_date.isoformat())
            
            # Execute query
            response = await db_query.limit(1000).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"Error getting candidate items: {e}")
            return []
    
    async def _calculate_similarities(self, target_item: Dict[str, Any], candidate_items: List[Dict[str, Any]], query: SimilarityQuery) -> List[SimilarItem]:
        """Calculate similarity scores for all candidate items"""
        similar_items = []
        
        # Prepare target text for vectorization
        target_text = self._prepare_text_for_similarity(target_item)
        
        # Fit vectorizer if not already fitted
        if not self.fitted_vectorizer and candidate_items:
            all_texts = [self._prepare_text_for_similarity(item) for item in candidate_items]
            self.vectorizer.fit(all_texts)
            self.fitted_vectorizer = True
        
        # Calculate vector similarities
        if query.use_vector_search:
            vector_similarities = await self._calculate_vector_similarities(target_text, candidate_items)
        else:
            vector_similarities = {}
        
        # Calculate keyword similarities
        if query.use_keyword_search:
            keyword_similarities = await self._calculate_keyword_similarities(target_item, candidate_items)
        else:
            keyword_similarities = {}
        
        # Calculate AI-enhanced similarities
        if query.use_ai_enhancement:
            ai_similarities = await self._calculate_ai_similarities(target_item, candidate_items)
        else:
            ai_similarities = {}
        
        # Combine all similarity scores
        for candidate in candidate_items:
            similar_item = await self._create_similar_item(target_item, candidate, vector_similarities, keyword_similarities, ai_similarities)
            similar_items.append(similar_item)
        
        return similar_items
    
    def _prepare_text_for_similarity(self, item: Dict[str, Any]) -> str:
        """Prepare text for similarity calculation"""
        try:
            # Combine all relevant text fields
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
            
            # Add features
            if item.get("features"):
                text_parts.extend(item["features"])
            
            # Add brand and model
            if item.get("brand"):
                text_parts.append(item["brand"])
            if item.get("model"):
                text_parts.append(item["model"])
            
            # Combine and clean
            combined_text = " ".join(text_parts).lower()
            combined_text = re.sub(r'[^\w\s]', ' ', combined_text)  # Remove punctuation
            combined_text = re.sub(r'\s+', ' ', combined_text)  # Normalize whitespace
            
            return combined_text.strip()
            
        except Exception as e:
            logger.error(f"Error preparing text for similarity: {e}")
            return ""
    
    async def _calculate_vector_similarities(self, target_text: str, candidate_items: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate cosine similarity using TF-IDF vectors"""
        try:
            # Transform target text
            target_vector = self.vectorizer.transform([target_text])
            
            # Transform candidate texts
            candidate_texts = [self._prepare_text_for_similarity(item) for item in candidate_items]
            candidate_vectors = self.vectorizer.transform(candidate_texts)
            
            # Calculate cosine similarities
            similarities = cosine_similarity(target_vector, candidate_vectors)[0]
            
            # Map to item IDs
            vector_similarities = {}
            for i, candidate in enumerate(candidate_items):
                item_id = candidate.get("item_id", str(i))
                vector_similarities[item_id] = float(similarities[i])
            
            return vector_similarities
            
        except Exception as e:
            logger.error(f"Error calculating vector similarities: {e}")
            return {}
    
    async def _calculate_keyword_similarities(self, target_item: Dict[str, Any], candidate_items: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate keyword-based similarity scores"""
        try:
            # Extract keywords from target item
            target_keywords = set()
            
            # Add title words
            if target_item.get("title"):
                target_keywords.update(target_item["title"].lower().split())
            
            # Add description words
            if target_item.get("description"):
                target_keywords.update(target_item["description"].lower().split())
            
            # Add explicit keywords
            if target_item.get("keywords"):
                target_keywords.update(kw.lower() for kw in target_item["keywords"])
            
            # Add brand and model
            if target_item.get("brand"):
                target_keywords.add(target_item["brand"].lower())
            if target_item.get("model"):
                target_keywords.add(target_item["model"].lower())
            
            # Calculate keyword matches for each candidate
            keyword_similarities = {}
            
            for candidate in candidate_items:
                candidate_keywords = set()
                
                # Extract candidate keywords
                if candidate.get("title"):
                    candidate_keywords.update(candidate["title"].lower().split())
                if candidate.get("description"):
                    candidate_keywords.update(candidate["description"].lower().split())
                if candidate.get("keywords"):
                    candidate_keywords.update(kw.lower() for kw in candidate["keywords"])
                if candidate.get("brand"):
                    candidate_keywords.add(candidate["brand"].lower())
                if candidate.get("model"):
                    candidate_keywords.add(candidate["model"].lower())
                
                # Calculate Jaccard similarity
                intersection = len(target_keywords.intersection(candidate_keywords))
                union = len(target_keywords.union(candidate_keywords))
                
                if union > 0:
                    similarity = intersection / union
                else:
                    similarity = 0.0
                
                item_id = candidate.get("item_id", str(candidate_items.index(candidate)))
                keyword_similarities[item_id] = similarity
            
            return keyword_similarities
            
        except Exception as e:
            logger.error(f"Error calculating keyword similarities: {e}")
            return {}
    
    async def _calculate_ai_similarities(self, target_item: Dict[str, Any], candidate_items: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate AI-enhanced similarity scores"""
        try:
            # Use Letta agent for AI similarity calculation
            agent_id = self.agent_ids["similarity"]
            agent = self.letta.agents.get(agent_id)
            
            # Prepare target item for AI
            target_prompt = f"""
            Target Item:
            Title: {target_item.get('title', '')}
            Description: {target_item.get('description', '')}
            Category: {target_item.get('category', '')}
            Brand: {target_item.get('brand', '')}
            Model: {target_item.get('model', '')}
            Features: {', '.join(target_item.get('features', []))}
            Keywords: {', '.join(target_item.get('keywords', []))}
            Price: ${target_item.get('price', 0)}
            Condition: {target_item.get('condition', '')}
            """
            
            # Process candidates in batches to avoid context limits
            batch_size = 5
            ai_similarities = {}
            
            for i in range(0, len(candidate_items), batch_size):
                batch = candidate_items[i:i + batch_size]
                
                # Prepare batch prompt
                candidates_prompt = ""
                for candidate in batch:
                    candidates_prompt += f"""
                    Candidate Item:
                    Title: {candidate.get('title', '')}
                    Description: {candidate.get('description', '')}
                    Category: {candidate.get('category', '')}
                    Brand: {candidate.get('brand', '')}
                    Model: {candidate.get('model', '')}
                    Features: {', '.join(candidate.get('features', []))}
                    Keywords: {', '.join(candidate.get('keywords', []))}
                    Price: ${candidate.get('price', 0)}
                    Condition: {candidate.get('condition', '')}
                    
                    ---
                    """
                
                # Create AI prompt
                prompt = f"""
                {target_prompt}
                
                Compare the target item with the following candidate items and provide similarity scores (0.0 to 1.0):
                
                {candidates_prompt}
                
                For each candidate, provide:
                1. Overall similarity score
                2. Key matching factors
                3. Confidence level
                
                Return JSON format:
                {{
                    "candidate_id": similarity_score,
                    "candidate_id2": similarity_score2,
                    ...
                }}
                """
                
                # Get AI response
                response = await agent.messages.create(content=prompt, role="user")
                
                # Parse response
                try:
                    ai_scores = json.loads(response.content)
                    ai_similarities.update(ai_scores)
                except json.JSONDecodeError:
                    logger.error("Failed to parse AI similarity response")
                    continue
            
            return ai_similarities
            
        except Exception as e:
            logger.error(f"Error calculating AI similarities: {e}")
            return {}
    
    async def _create_similar_item(self, target_item: Dict[str, Any], candidate: Dict[str, Any], vector_similarities: Dict[str, float], keyword_similarities: Dict[str, float], ai_similarities: Dict[str, float]) -> SimilarItem:
        """Create a SimilarItem object with all similarity scores"""
        try:
            item_id = candidate.get("item_id", "")
            
            # Calculate individual similarity scores
            similarity_scores = []
            
            # Vector similarity
            vector_score = vector_similarities.get(item_id, 0.0)
            if vector_score > 0:
                similarity_scores.append(SimilarityScore(
                    item_id=item_id,
                    similarity_type=SimilarityType.OVERALL,
                    score=vector_score,
                    matched_fields=["vector_similarity"],
                    confidence=0.8,
                    source="vector"
                ))
            
            # Keyword similarity
            keyword_score = keyword_similarities.get(item_id, 0.0)
            if keyword_score > 0:
                similarity_scores.append(SimilarityScore(
                    item_id=item_id,
                    similarity_type=SimilarityType.KEYWORDS,
                    score=keyword_score,
                    matched_fields=["keyword_matching"],
                    confidence=0.7,
                    source="keyword"
                ))
            
            # AI similarity
            ai_score = ai_similarities.get(item_id, 0.0)
            if ai_score > 0:
                similarity_scores.append(SimilarityScore(
                    item_id=item_id,
                    similarity_type=SimilarityType.OVERALL,
                    score=ai_score,
                    matched_fields=["ai_analysis"],
                    confidence=0.9,
                    source="ai"
                ))
            
            # Calculate overall similarity (weighted average)
            all_scores = [score.score for score in similarity_scores]
            overall_similarity = sum(all_scores) / len(all_scores) if all_scores else 0.0
            
            # Create SimilarItem object
            similar_item = SimilarItem(
                item_id=item_id,
                platform=candidate.get("platform", ""),
                title=candidate.get("title", ""),
                description=candidate.get("description", ""),
                category=candidate.get("category", ""),
                price=candidate.get("price", 0),
                condition=candidate.get("condition", ""),
                brand=candidate.get("brand", ""),
                model=candidate.get("model", ""),
                features=candidate.get("features", []),
                keywords=candidate.get("keywords", []),
                similarity_scores=similarity_scores,
                overall_similarity=overall_similarity,
                metadata_completeness=len([k for k, v in candidate.items() if