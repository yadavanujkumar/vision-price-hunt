from typing import List, Dict
import re
import logging
from difflib import SequenceMatcher

from app.models.schemas import ProductOffer, ProductInfo

logger = logging.getLogger(__name__)

class NormalizationService:
    def __init__(self):
        # Common product name patterns to normalize
        self.brand_aliases = {
            "apple": ["apple inc", "apple computer"],
            "samsung": ["samsung electronics"],
            "microsoft": ["microsoft corp", "microsoft corporation"],
            "google": ["alphabet inc", "google llc"],
        }
        
        # Common size/model variations
        self.size_patterns = [
            r'\b(\d+)\s*(gb|tb|mb)\b',  # Storage sizes
            r'\b(\d+)\s*(inch|in|")\b',  # Screen sizes
            r'\b(\d+)\s*(oz|lb|kg|g)\b',  # Weight
        ]
        
        # Color patterns
        self.color_patterns = [
            r'\b(black|white|red|blue|green|yellow|purple|pink|grey|gray|silver|gold)\b'
        ]

    def normalize_product_name(self, name: str) -> str:
        """Normalize product name for better matching"""
        try:
            # Convert to lowercase
            normalized = name.lower().strip()
            
            # Remove special characters except spaces and alphanumeric
            normalized = re.sub(r'[^\w\s]', ' ', normalized)
            
            # Remove extra whitespace
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            
            # Remove common stopwords
            stopwords = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
            words = normalized.split()
            words = [word for word in words if word not in stopwords]
            
            return ' '.join(words)
            
        except Exception as e:
            logger.error(f"Error normalizing product name: {e}")
            return name.lower()

    def extract_product_features(self, product_info: ProductInfo) -> Dict[str, str]:
        """Extract key features from product information"""
        features = {}
        
        try:
            text = (product_info.description or "") + " " + (product_info.name or "")
            text = text.lower()
            
            # Extract storage size
            for pattern in self.size_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    if 'gb' in pattern or 'tb' in pattern or 'mb' in pattern:
                        features['storage'] = matches[0]
                    elif 'inch' in pattern or 'in' in pattern:
                        features['screen_size'] = matches[0]
                    elif 'oz' in pattern or 'lb' in pattern or 'kg' in pattern:
                        features['weight'] = matches[0]
            
            # Extract color
            color_matches = re.findall(self.color_patterns[0], text, re.IGNORECASE)
            if color_matches:
                features['color'] = color_matches[0]
            
            # Extract brand (normalized)
            if product_info.brand:
                brand_lower = product_info.brand.lower()
                for main_brand, aliases in self.brand_aliases.items():
                    if brand_lower == main_brand or brand_lower in aliases:
                        features['brand'] = main_brand
                        break
                else:
                    features['brand'] = brand_lower
            
            # Extract category
            if product_info.category:
                features['category'] = product_info.category.lower()
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting product features: {e}")
            return {}

    def calculate_product_similarity(self, product1: ProductInfo, product2: ProductInfo) -> float:
        """Calculate similarity between two products"""
        try:
            # Normalize names
            name1 = self.normalize_product_name(product1.name or "")
            name2 = self.normalize_product_name(product2.name or "")
            
            # Basic name similarity
            name_similarity = SequenceMatcher(None, name1, name2).ratio()
            
            # Extract features
            features1 = self.extract_product_features(product1)
            features2 = self.extract_product_features(product2)
            
            # Calculate feature similarity
            feature_similarity = 0.0
            total_features = 0
            
            for feature in set(features1.keys()).union(set(features2.keys())):
                total_features += 1
                if feature in features1 and feature in features2:
                    if features1[feature] == features2[feature]:
                        feature_similarity += 1.0
                    else:
                        # Partial similarity for similar values
                        feature_similarity += SequenceMatcher(None, features1[feature], features2[feature]).ratio() * 0.5
            
            if total_features > 0:
                feature_similarity /= total_features
            
            # Simple text similarity using SequenceMatcher
            text1 = f"{product1.name} {product1.brand or ''} {product1.description or ''}"
            text2 = f"{product2.name} {product2.brand or ''} {product2.description or ''}"
            text_similarity = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
            
            # Weighted average
            weights = {
                'name': 0.4,
                'features': 0.3,
                'text': 0.3
            }
            
            final_similarity = (
                name_similarity * weights['name'] +
                feature_similarity * weights['features'] +
                text_similarity * weights['text']
            )
            
            return min(final_similarity, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating product similarity: {e}")
            return 0.0

    def normalize_offers(self, offers: List[ProductOffer]) -> List[ProductOffer]:
        """Normalize all offers for consistent processing"""
        normalized_offers = []
        
        for offer in offers:
            try:
                # Create normalized copy
                normalized_offer = ProductOffer(
                    product_info=ProductInfo(
                        name=self.normalize_product_name(offer.product_info.name or ""),
                        brand=offer.product_info.brand,
                        category=offer.product_info.category,
                        description=offer.product_info.description,
                        extracted_text=offer.product_info.extracted_text,
                        confidence=offer.product_info.confidence
                    ),
                    price_info=offer.price_info,
                    similarity_score=offer.similarity_score,
                    image_url=offer.image_url
                )
                
                normalized_offers.append(normalized_offer)
                
            except Exception as e:
                logger.error(f"Error normalizing offer: {e}")
                # Add original offer if normalization fails
                normalized_offers.append(offer)
        
        return normalized_offers

# Global instance
normalization_service = NormalizationService()