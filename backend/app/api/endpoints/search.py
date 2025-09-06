from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
import time
import uuid
import logging
from typing import Optional

from app.models.schemas import SearchResponse, ProductInfo, ErrorResponse
from app.services.vision import vision_service
from app.services.scraper import scraping_service
from app.services.ranking import ranking_service
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/search", response_model=SearchResponse)
async def search_products(
    product_info: ProductInfo,
    background_tasks: BackgroundTasks
):
    """
    Search for products and prices based on product information
    
    - **product_info**: Product information extracted from image or provided directly
    
    Returns ranked list of exact matches and similar products with prices
    """
    start_time = time.time()
    query_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Starting product search for query {query_id}")
        
        # Validate input
        if not product_info.name and not product_info.description:
            raise HTTPException(
                status_code=400,
                detail="Product name or description is required"
            )
        
        # Scrape all sources for prices
        logger.info("Scraping price sources...")
        all_offers = await scraping_service.scrape_all_sources(product_info)
        
        # Filter and validate offers
        valid_offers = scraping_service.filter_and_validate_offers(all_offers)
        
        logger.info(f"Found {len(valid_offers)} valid offers")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create ranked search response
        response = ranking_service.create_search_response(
            query_product=product_info,
            all_offers=valid_offers,
            processing_time=processing_time,
            query_id=query_id
        )
        
        logger.info(f"Search completed for query {query_id} in {processing_time:.2f}s")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error in product search: {e}")
        
        # Return empty response with error information
        return SearchResponse(
            exact_matches=[],
            similar_products=[],
            processing_time=processing_time,
            query_id=query_id
        )

@router.get("/search/{query_id}")
async def get_search_results(query_id: str):
    """
    Get cached search results by query ID
    
    - **query_id**: Query ID from previous search
    
    Note: This is a placeholder - in production you'd implement result caching
    """
    try:
        # This is a placeholder implementation
        # In production, you'd store and retrieve results from a cache/database
        return {
            "message": f"Search results for query {query_id}",
            "note": "Result caching not implemented in this demo"
        }
    
    except Exception as e:
        logger.error(f"Error retrieving search results: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve search results")

@router.get("/search/similar/{product_name}")
async def search_similar_products(
    product_name: str,
    limit: int = Query(default=10, le=50, description="Maximum number of results"),
    category: Optional[str] = Query(default=None, description="Product category filter")
):
    """
    Search for similar products by name
    
    - **product_name**: Name of the product to find similar items for
    - **limit**: Maximum number of results (max 50)
    - **category**: Optional category filter
    """
    start_time = time.time()
    query_id = str(uuid.uuid4())
    
    try:
        # Create ProductInfo from parameters
        product_info = ProductInfo(
            name=product_name,
            category=category,
            description=f"Similar products for {product_name}"
        )
        
        # Search for products
        all_offers = await scraping_service.scrape_all_sources(product_info)
        valid_offers = scraping_service.filter_and_validate_offers(all_offers)
        
        # Get only similar products (lower similarity threshold)
        similar_offers = []
        for offer in valid_offers:
            similarity = vision_service.calculate_similarity(
                product_name, 
                offer.product_info.name or ""
            )
            if similarity > 0.3:  # Lower threshold for similar products
                offer.similarity_score = similarity
                similar_offers.append(offer)
        
        # Rank and limit results
        ranked_offers = ranking_service.rank_offers(similar_offers)
        limited_offers = ranked_offers[:limit]
        
        processing_time = time.time() - start_time
        
        return {
            "query_id": query_id,
            "product_name": product_name,
            "similar_products": limited_offers,
            "total_found": len(ranked_offers),
            "processing_time": processing_time
        }
    
    except Exception as e:
        logger.error(f"Error searching similar products: {e}")
        raise HTTPException(status_code=500, detail="Failed to search similar products")

@router.get("/search/best-deals")
async def get_best_deals(
    category: Optional[str] = Query(default=None, description="Product category"),
    limit: int = Query(default=5, le=20, description="Number of deals to return")
):
    """
    Get current best deals across all categories
    
    - **category**: Optional category filter
    - **limit**: Number of deals to return (max 20)
    
    Note: This is a demo endpoint with mock data
    """
    try:
        # Create a generic product info for searching
        product_info = ProductInfo(
            name="popular products",
            category=category,
            description="Best deals search"
        )
        
        # Get offers from all sources
        all_offers = await scraping_service.scrape_all_sources(product_info)
        valid_offers = scraping_service.filter_and_validate_offers(all_offers)
        
        # Get best deals
        best_deals = ranking_service.get_best_deals(valid_offers, limit)
        
        return {
            "best_deals": best_deals,
            "category": category,
            "total_deals": len(best_deals)
        }
    
    except Exception as e:
        logger.error(f"Error getting best deals: {e}")
        raise HTTPException(status_code=500, detail="Failed to get best deals")

@router.get("/search/health")
async def search_health():
    """Health check for search service"""
    try:
        # Test basic functionality
        test_product = ProductInfo(name="test product")
        
        # Quick test of vision service
        vision_available = vision_service.text_model is not None
        
        return {
            "status": "healthy",
            "vision_service": "available" if vision_available else "unavailable",
            "scraping_service": "available",
            "ranking_service": "available",
            "similarity_threshold": settings.similarity_threshold,
            "max_similar_products": settings.max_similar_products
        }
    
    except Exception as e:
        logger.error(f"Search service health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }