from typing import List, Dict, Tuple
import logging
from datetime import datetime

from app.models.schemas import ProductOffer, ProductInfo, SearchResponse
from app.services.normalizer import normalization_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class RankingService:
    def __init__(self):
        # Weights for ranking factors
        self.ranking_weights = {
            'price': 0.3,           # Lower price = better rank
            'similarity': 0.4,      # Higher similarity = better rank
            'source_trust': 0.1,    # Trusted sources = better rank
            'availability': 0.1,    # In stock = better rank
            'recency': 0.1         # Recent data = better rank
        }
        
        # Source trust scores
        self.source_trust_scores = {
            'amazon': 0.9,
            'ebay': 0.8,
            'bestbuy': 0.85,
            'walmart': 0.8,
            'target': 0.75,
            'generic store': 0.5
        }
    
    def calculate_price_score(self, price: float, all_prices: List[float]) -> float:
        """Calculate price score (lower price = higher score)"""
        try:
            if not all_prices or price <= 0:
                return 0.0
            
            min_price = min(all_prices)
            max_price = max(all_prices)
            
            if min_price == max_price:
                return 1.0
            
            # Normalize price to 0-1 range (inverted so lower price = higher score)
            normalized_price = 1.0 - ((price - min_price) / (max_price - min_price))
            return max(0.0, min(1.0, normalized_price))
            
        except Exception as e:
            logger.error(f"Error calculating price score: {e}")
            return 0.0

    def calculate_source_trust_score(self, source: str) -> float:
        """Calculate trust score for the source"""
        try:
            source_lower = source.lower()
            return self.source_trust_scores.get(source_lower, 0.5)
        except Exception as e:
            logger.error(f"Error calculating source trust score: {e}")
            return 0.5

    def calculate_availability_score(self, availability: str) -> float:
        """Calculate availability score"""
        try:
            availability_lower = availability.lower()
            if 'in_stock' in availability_lower or 'available' in availability_lower:
                return 1.0
            elif 'limited' in availability_lower:
                return 0.7
            elif 'pre_order' in availability_lower:
                return 0.5
            else:
                return 0.2
        except Exception as e:
            logger.error(f"Error calculating availability score: {e}")
            return 0.5

    def calculate_recency_score(self, last_updated: datetime) -> float:
        """Calculate recency score (more recent = higher score)"""
        try:
            now = datetime.now()
            time_diff = (now - last_updated).total_seconds()
            
            # Score decreases with time
            # 100% for < 1 hour, 90% for < 1 day, 70% for < 1 week, 50% for older
            if time_diff < 3600:  # 1 hour
                return 1.0
            elif time_diff < 86400:  # 1 day
                return 0.9
            elif time_diff < 604800:  # 1 week
                return 0.7
            else:
                return 0.5
                
        except Exception as e:
            logger.error(f"Error calculating recency score: {e}")
            return 0.5

    def calculate_overall_score(self, offer: ProductOffer, all_prices: List[float]) -> float:
        """Calculate overall ranking score for an offer"""
        try:
            # Calculate individual scores
            price_score = self.calculate_price_score(offer.price_info.price, all_prices)
            similarity_score = offer.similarity_score
            source_trust_score = self.calculate_source_trust_score(offer.price_info.source)
            availability_score = self.calculate_availability_score(offer.price_info.availability)
            recency_score = self.calculate_recency_score(offer.price_info.last_updated)
            
            # Calculate weighted overall score
            overall_score = (
                price_score * self.ranking_weights['price'] +
                similarity_score * self.ranking_weights['similarity'] +
                source_trust_score * self.ranking_weights['source_trust'] +
                availability_score * self.ranking_weights['availability'] +
                recency_score * self.ranking_weights['recency']
            )
            
            return max(0.0, min(1.0, overall_score))
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 0.0

    def rank_offers(self, offers: List[ProductOffer]) -> List[ProductOffer]:
        """Rank offers based on multiple criteria"""
        try:
            if not offers:
                return []
            
            # Extract all prices for normalization
            all_prices = [offer.price_info.price for offer in offers if offer.price_info.price > 0]
            
            # Calculate scores for each offer
            scored_offers = []
            for offer in offers:
                score = self.calculate_overall_score(offer, all_prices)
                scored_offers.append((offer, score))
            
            # Sort by score (highest first)
            scored_offers.sort(key=lambda x: x[1], reverse=True)
            
            # Return sorted offers
            return [offer for offer, score in scored_offers]
            
        except Exception as e:
            logger.error(f"Error ranking offers: {e}")
            return offers

    def separate_exact_and_similar(self, query_product: ProductInfo, offers: List[ProductOffer]) -> Tuple[List[ProductOffer], List[ProductOffer]]:
        """Separate offers into exact matches and similar products"""
        exact_matches = []
        similar_products = []
        
        try:
            for offer in offers:
                # Calculate similarity with query product
                similarity = normalization_service.calculate_product_similarity(
                    query_product, offer.product_info
                )
                
                # Update similarity score in offer
                offer.similarity_score = similarity
                
                # Classify as exact or similar based on threshold
                if similarity >= settings.similarity_threshold:
                    exact_matches.append(offer)
                else:
                    similar_products.append(offer)
            
            # Rank both lists
            exact_matches = self.rank_offers(exact_matches)
            similar_products = self.rank_offers(similar_products)
            
            # Limit similar products
            similar_products = similar_products[:settings.max_similar_products]
            
            return exact_matches, similar_products
            
        except Exception as e:
            logger.error(f"Error separating exact and similar products: {e}")
            return offers, []

    def create_search_response(
        self, 
        query_product: ProductInfo, 
        all_offers: List[ProductOffer], 
        processing_time: float, 
        query_id: str
    ) -> SearchResponse:
        """Create final search response with ranked results"""
        try:
            # Normalize offers
            normalized_offers = normalization_service.normalize_offers(all_offers)
            
            # Separate exact matches from similar products
            exact_matches, similar_products = self.separate_exact_and_similar(
                query_product, normalized_offers
            )
            
            # Create response
            response = SearchResponse(
                exact_matches=exact_matches,
                similar_products=similar_products,
                processing_time=processing_time,
                query_id=query_id
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating search response: {e}")
            return SearchResponse(
                exact_matches=[],
                similar_products=[],
                processing_time=processing_time,
                query_id=query_id
            )

    def get_best_deals(self, offers: List[ProductOffer], limit: int = 5) -> List[ProductOffer]:
        """Get best deals based on price and quality"""
        try:
            # Filter for in-stock items only
            available_offers = [
                offer for offer in offers 
                if 'in_stock' in offer.price_info.availability.lower()
            ]
            
            # Rank by overall score
            ranked_offers = self.rank_offers(available_offers)
            
            # Return top deals
            return ranked_offers[:limit]
            
        except Exception as e:
            logger.error(f"Error getting best deals: {e}")
            return offers[:limit]

# Global instance
ranking_service = RankingService()