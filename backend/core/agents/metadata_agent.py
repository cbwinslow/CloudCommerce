import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from PIL import Image
import io
import base64
from letta import LettaClient
from litellm import completion
import hashlib
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QualityLevel(Enum):
    POOR = 1
    FAIR = 2
    GOOD = 3
    EXCELLENT = 4
    PERFECT = 5

@dataclass
class MetadataField:
    name: str
    value: Any
    confidence: float
    source: str  # "ai", "similar", "manual", "auto"
    verified: bool = False

@dataclass
class QualityAssessment:
    overall_score: float
    title_quality: float
    description_quality: float
    image_quality: float
    metadata_completeness: float
    price_reasonableness: float
    category_accuracy: float
    condition_accuracy: float
    brand_identification: float
    model_identification: float
    features_extraction: float
    specifications_extraction: float
    keywords_relevance: float
    target_audience_accuracy: float
    seasonality_accuracy: float
    market_value_accuracy: float

@dataclass
class EnhancedMetadata:
    title: str
    description: str
    category: str
    condition: str
    brand: str
    model: str
    features: List[str]
    specifications: Dict[str, Any]
    keywords: List[str]
    target_audience: str
    seasonality: str
    estimated_market_value: float
    confidence_score: float
    quality_score: float
    metadata_fields: Dict[str, MetadataField]
    processing_time: float
    model_version: str

class MetadataAgent:
    def __init__(self, supabase_client, letta_client: LettaClient):
        self.supabase = supabase_client
        self.letta = letta_client
        self.session: Optional[aiohttp.ClientSession] = None
        self.model_version = "1.0.0"
        
        # Initialize agent IDs
        self.agent_ids = {
            "metadata": os.getenv("LETTA_METADATA_AGENT_ID"),
            "quality": os.getenv("LETTA_QUALITY_AGENT_ID"),
            "similarity": os.getenv("LETTA_SIMILARITY_AGENT_ID"),
            "merge": os.getenv("LETTA_MERGE_AGENT_ID"),
            "categorization": os.getenv("LETTA_CATEGORIZATION_AGENT_ID")
        }
        
        # Quality thresholds
        self.quality_thresholds = {
            QualityLevel.POOR: 0.0,
            QualityLevel.FAIR: 0.4,
            QualityLevel.GOOD: 0.6,
            QualityLevel.EXCELLENT: 0.8,
            QualityLevel.PERFECT: 0.95
        }
    
    async def process_item(self, item_data: Dict[str, Any], similar_items: List[Dict[str, Any]] = None) -> EnhancedMetadata:
        """Process an item and generate enhanced metadata"""
        start_time = datetime.now()
        
        try:
            # Extract basic information
            title = item_data.get("title", "")
            description = item_data.get("description", "")
            images = item_data.get("images", [])
            price = item_data.get("price", 0)
            category = item_data.get("category", "")
            condition = item_data.get("condition", "")
            
            # Step 1: AI-powered metadata extraction
            ai_metadata = await self._extract_metadata_with_ai(title, description, images, price, category, condition)
            
            # Step 2: Similarity-based metadata enhancement
            if similar_items:
                similarity_metadata = await self._enhance_with_similarity_metadata(ai_metadata, similar_items)
                ai_metadata.update(similarity_metadata)
            
            # Step 3: Quality assessment
            quality_assessment = await self._assess_quality(ai_metadata, title, description, images, price)
            
            # Step 4: Metadata validation and refinement
            validated_metadata = await self._validate_and_refine_metadata(ai_metadata, quality_assessment)
            
            # Step 5: Calculate final scores
            confidence_score = self._calculate_confidence_score(validated_metadata, quality_assessment)
            quality_score = self._calculate_quality_score(quality_assessment)
            
            # Create enhanced metadata object
            enhanced_metadata = EnhancedMetadata(
                title=validated_metadata.get("title", title),
                description=validated_metadata.get("description", description),
                category=validated_metadata.get("category", category),
                condition=validated_metadata.get("condition", condition),
                brand=validated_metadata.get("brand", ""),
                model=validated_metadata.get("model", ""),
                features=validated_metadata.get("features", []),
                specifications=validated_metadata.get("specifications", {}),
                keywords=validated_metadata.get("keywords", []),
                target_audience=validated_metadata.get("target_audience", ""),
                seasonality=validated_metadata.get("seasonality", ""),
                estimated_market_value=validated_metadata.get("estimated_market_value", 0),
                confidence_score=confidence_score,
                quality_score=quality_score,
                metadata_fields=validated_metadata.get("metadata_fields", {}),
                processing_time=(datetime.now() - start_time).total_seconds(),
                model_version=self.model_version
            )
            
            return enhanced_metadata
            
        except Exception as e:
            logger.error(f"Error processing item: {e}")
            raise
    
    async def _extract_metadata_with_ai(self, title: str, description: str, images: List[str], price: float, category: str, condition: str) -> Dict[str, Any]:
        """Extract metadata using AI agents"""
        try:
            # Use Letta agent for metadata extraction
            agent_id = self.agent_ids["metadata"]
            agent = self.letta.agents.get(agent_id)
            
            # Prepare image analysis if images are available
            image_analysis = ""
            if images:
                image_analysis = await self._analyze_images_with_ai(images)
            
            # Create comprehensive prompt
            prompt = f"""
            Analyze this item and extract comprehensive metadata:
            
            Title: {title}
            Description: {description}
            Category: {category}
            Condition: {condition}
            Price: ${price}
            
            Image Analysis: {image_analysis}
            
            Generate JSON with the following fields:
            - enhanced_title: More descriptive and SEO-friendly title
            - description: Enhanced description with key features
            - category: Specific category (if different from input)
            - condition: Detailed condition assessment
            - brand: Brand name (if identifiable)
            - model: Model number or version (if applicable)
            - features: List of key features (5-10 items)
            - specifications: Detailed specifications as key-value pairs
            - keywords: Relevant keywords for search (10-15 items)
            - target_audience: Who this item is for
            - seasonality: Seasonal relevance (e.g., "summer", "winter", "year-round")
            - estimated_market_value: Estimated market value based on similar items
            - metadata_fields: Detailed field-by-field analysis with confidence scores
            
            Be specific and detailed. Use the image analysis to extract visual details.
            """
            
            # Get AI response
            response = await agent.messages.create(content=prompt, role="user")
            
            # Parse response as JSON
            try:
                metadata = json.loads(response.content)
                return metadata
            except json.JSONDecodeError:
                logger.error("Failed to parse AI response as JSON")
                return {}
            
        except Exception as e:
            logger.error(f"Error extracting metadata with AI: {e}")
            return {}
    
    async def _analyze_images_with_ai(self, images: List[str]) -> str:
        """Analyze images using AI vision model"""
        try:
            # Use OpenRouter for image analysis
            image_analysis_results = []
            
            for image_url in images[:3]:  # Analyze first 3 images
                try:
                    prompt = f"""
                    Analyze this image and provide detailed information about:
                    - Product type and category
                    - Brand and model (if visible)
                    - Key features and specifications
                    - Condition assessment
                    - Any text or labels visible
                    - Color, size, and other physical attributes
                    """
                    
                    # Use OpenRouter vision model
                    response = completion(
                        model="openrouter/llava-13b-v1.6",
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": image_url}}
                            ]
                        }],
                        max_tokens=500
                    )
                    
                    image_analysis_results.append(response.choices[0].message.content)
                    
                except Exception as e:
                    logger.error(f"Error analyzing image: {e}")
                    continue
            
            return "\n".join(image_analysis_results)
            
        except Exception as e:
            logger.error(f"Error analyzing images with AI: {e}")
            return ""
    
    async def _enhance_with_similarity_metadata(self, ai_metadata: Dict[str, Any], similar_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhance metadata using similar items"""
        try:
            # Use Letta agent for similarity-based enhancement
            agent_id = self.agent_ids["similarity"]
            agent = self.letta.agents.get(agent_id)
            
            # Prepare similar items data
            similar_data = json.dumps(similar_items[:5], indent=2)  # Use top 5 similar items
            
            prompt = f"""
            Enhance the following metadata using information from similar items:
            
            Current Metadata: {json.dumps(ai_metadata, indent=2)}
            
            Similar Items: {similar_data}
            
            Return enhanced JSON metadata by:
            1. Filling in missing information from similar items
            2. Improving category classification
            3. Adding missing features and specifications
            4. Enhancing keywords and tags
            5. Providing better condition assessment
            6. Estimating market value based on similar items
            
            Only include information you're confident about (confidence > 0.7).
            Mark enhanced fields with source: "similar"
            """
            
            response = await agent.messages.create(content=prompt, role="user")
            
            try:
                enhanced_metadata = json.loads(response.content)
                return enhanced_metadata
            except json.JSONDecodeError:
                logger.error("Failed to parse similarity enhancement response")
                return {}
            
        except Exception as e:
            logger.error(f"Error enhancing with similarity metadata: {e}")
            return {}
    
    async def _assess_quality(self, metadata: Dict[str, Any], title: str, description: str, images: List[str], price: float) -> QualityAssessment:
        """Assess the quality of the item and metadata"""
        try:
            # Use Letta agent for quality assessment
            agent_id = self.agent_ids["quality"]
            agent = self.letta.agents.get(agent_id)
            
            prompt = f"""
            Assess the quality of this item and its metadata:
            
            Title: {title}
            Description: {description}
            Images: {len(images)} images
            Price: ${price}
            Metadata: {json.dumps(metadata, indent=2)}
            
            Provide a JSON object with quality scores (0.0 to 1.0) for:
            - title_quality: How descriptive and complete is the title?
            - description_quality: How detailed and informative is the description?
            - image_quality: How good are the images (quantity, quality, relevance)?
            - metadata_completeness: How complete is the metadata?
            - price_reasonableness: Is the price reasonable for the item?
            - category_accuracy: How accurate is the category classification?
            - condition_accuracy: How accurate is the condition assessment?
            - brand_identification: How well was the brand identified?
            - model_identification: How well was the model identified?
            - features_extraction: How well were features extracted?
            - specifications_extraction: How well were specifications extracted?
            - keywords_relevance: How relevant are the keywords?
            - target_audience_accuracy: How accurate is the target audience?
            - seasonality_accuracy: How accurate is the seasonality assessment?
            - market_value_accuracy: How accurate is the market value estimate?
            
            Also provide an overall_score (0.0 to 1.0).
            """
            
            response = await agent.messages.create(content=prompt, role="user")
            
            try:
                quality_data = json.loads(response.content)
                return QualityAssessment(
                    overall_score=quality_data.get("overall_score", 0.0),
                    title_quality=quality_data.get("title_quality", 0.0),
                    description_quality=quality_data.get("description_quality", 0.0),
                    image_quality=quality_data.get("image_quality", 0.0),
                    metadata_completeness=quality_data.get("metadata_completeness", 0.0),
                    price_reasonableness=quality_data.get("price_reasonableness", 0.0),
                    category_accuracy=quality_data.get("category_accuracy", 0.0),
                    condition_accuracy=quality_data.get("condition_accuracy", 0.0),
                    brand_identification=quality_data.get("brand_identification", 0.0),
                    model_identification=quality_data.get("model_identification", 0.0),
                    features_extraction=quality_data.get("features_extraction", 0.0),
                    specifications_extraction=quality_data.get("specifications_extraction", 0.0),
                    keywords_relevance=quality_data.get("keywords_relevance", 0.0),
                    target_audience_accuracy=quality_data.get("target_audience_accuracy", 0.0),
                    seasonality_accuracy=quality_data.get("seasonality_accuracy", 0.0),
                    market_value_accuracy=quality_data.get("market_value_accuracy", 0.0)
                )
            except json.JSONDecodeError:
                logger.error("Failed to parse quality assessment response")
                return QualityAssessment(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            
        except Exception as e:
            logger.error(f"Error assessing quality: {e}")
            return QualityAssessment(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    
    async def _validate_and_refine_metadata(self, metadata: Dict[str, Any], quality_assessment: QualityAssessment) -> Dict[str, Any]:
        """Validate and refine metadata based on quality assessment"""
        try:
            # Use Letta agent for validation and refinement
            agent_id = self.agent_ids["merge"]
            agent = self.letta.agents.get(agent_id)
            
            prompt = f"""
            Validate and refine the following metadata based on quality assessment:
            
            Current Metadata: {json.dumps(metadata, indent=2)}
            
            Quality Assessment: {asdict(quality_assessment)}
            
            Tasks:
            1. Remove or improve low-quality fields (score < 0.5)
            2. Enhance medium-quality fields (0.5 <= score < 0.8)
            3. Keep high-quality fields (score >= 0.8)
            4. Add missing but important information
            5. Ensure consistency across all fields
            6. Verify that all information is accurate and reliable
            
            Return refined JSON metadata with improved quality scores.
            """
            
            response = await agent.messages.create(content=prompt, role="user")
            
            try:
                refined_metadata = json.loads(response.content)
                return refined_metadata
            except json.JSONDecodeError:
                logger.error("Failed to parse metadata refinement response")
                return metadata
            
        except Exception as e:
            logger.error(f"Error validating and refining metadata: {e}")
            return metadata
    
    def _calculate_confidence_score(self, metadata: Dict[str, Any], quality_assessment: QualityAssessment) -> float:
        """Calculate overall confidence score"""
        try:
            factors = []
            
            # Data completeness
            completeness = len([k for k, v in metadata.items() if v and v != ""]) / 10
            factors.append(min(completeness, 1.0))
            
            # Quality assessment
            quality_factor = quality_assessment.overall_score
            factors.append(quality_factor)
            
            # Metadata field confidence
            if "metadata_fields" in metadata:
                field_confidences = [field.confidence for field in metadata["metadata_fields"].values()]
                if field_confidences:
                    avg_field_confidence = sum(field_confidences) / len(field_confidences)
                    factors.append(avg_field_confidence)
            
            # Calculate weighted average
            confidence_score = sum(factors) / len(factors) if factors else 0.0
            
            return round(confidence_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.0
    
    def _calculate_quality_score(self, quality_assessment: QualityAssessment) -> float:
        """Calculate overall quality score"""
        try:
            # Weighted average of all quality metrics
            weights = {
                "title_quality": 0.1,
                "description_quality": 0.15,
                "image_quality": 0.1,
                "metadata_completeness": 0.15,
                "price_reasonableness": 0.05,
                "category_accuracy": 0.05,
                "condition_accuracy": 0.05,
                "brand_identification": 0.05,
                "model_identification": 0.05,
                "features_extraction": 0.05,
                "specifications_extraction": 0.05,
                "keywords_relevance": 0.05,
                "target_audience_accuracy": 0.03,
                "seasonality_accuracy": 0.02,
                "market_value_accuracy": 0.05
            }
            
            total_score = 0.0
            total_weight = 0.0
            
            for metric, weight in weights.items():
                score = getattr(quality_assessment, metric, 0.0)
                total_score += score * weight
                total_weight += weight
            
            quality_score = total_score / total_weight if total_weight > 0 else 0.0
            
            return round(quality_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.0
    
    def get_quality_level(self, quality_score: float) -> QualityLevel:
        """Get quality level from quality score"""
        if quality_score >= self.quality_thresholds[QualityLevel.PERFECT]:
            return QualityLevel.PERFECT
        elif quality_score >= self.quality_thresholds[QualityLevel.EXCELLENT]:
            return QualityLevel.EXCELLENT
        elif quality_score >= self.quality_thresholds[QualityLevel.GOOD]:
            return QualityLevel.GOOD
        elif quality_score >= self.quality_thresholds[QualityLevel.FAIR]:
            return QualityLevel.FAIR
        else:
            return QualityLevel.POOR
    
    async def batch_process_items(self, items: List[Dict[str, Any]], similar_items_map: Dict[str, List[Dict[str, Any]]] = None) -> List[EnhancedMetadata]:
        """Process multiple items in batch"""
        results = []
        
        for item in items:
            try:
                # Get similar items for this item
                similar_items = similar_items_map.get(item.get("id"), []) if similar_items_map else []
                
                # Process item
                enhanced_metadata = await self.process_item(item, similar_items)
                results.append(enhanced_metadata)
                
                # Add small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing item {item.get('id', 'unknown')}: {e}")
                continue
        
        return results
    
    async def update_model_version(self, new_version: str):
        """Update the model version"""
        self.model_version = new_version
        logger.info(f"Updated model version to {new_version}")
    
    async def get_processing_statistics(self, processed_items: List[EnhancedMetadata]) -> Dict[str, Any]:
        """Get processing statistics"""
        try:
            if not processed_items:
                return {}
            
            stats = {
                "total_items": len(processed_items),
                "average_quality_score": sum(item.quality_score for item in processed_items) / len(processed_items),
                "average_confidence_score": sum(item.confidence_score for item in processed_items) / len(processed_items),
                "average_processing_time": sum(item.processing_time for item in processed_items) / len(processed_items),
                "quality_distribution": {
                    "poor": sum(1 for item in processed_items if item.quality_score < 0.4),
                    "fair": sum(1 for item in processed_items if 0.4 <= item.quality_score < 0.6),
                    "good": sum(1 for item in processed_items if 0.6 <= item.quality_score < 0.8),
                    "excellent": sum(1 for item in processed_items if 0.8 <= item.quality_score < 0.95),
                    "perfect": sum(1 for item in processed_items if item.quality_score >= 0.95)
                },
                "confidence_distribution": {
                    "low": sum(1 for item in processed_items if item.confidence_score < 0.5),
                    "medium": sum(1 for item in processed_items if 0.5 <= item.confidence_score < 0.8),
                    "high": sum(1 for item in processed_items if item.confidence_score >= 0.8)
                },
                "common_brands": self._get_most_common_values(processed_items, "brand"),
                "common_categories": self._get_most_common_values(processed_items, "category"),
                "common_conditions": self._get_most_common_values(processed_items, "condition")
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating processing statistics: {e}")
            return {}
    
    def _get_most_common_values(self, items: List[EnhancedMetadata], field: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most common values for a field"""
        try:
            value_counts = {}
            
            for item in items:
                value = getattr(item, field, "")
                if value:
                    value_counts[value] = value_counts.get(value, 0) + 1
            
            # Sort by count and return top values
            sorted_values = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)
            
            return [{"value": value, "count": count} for value, count in sorted_values[:limit]]
            
        except Exception as e:
            logger.error(f"Error getting most common values: {e}")
            return []