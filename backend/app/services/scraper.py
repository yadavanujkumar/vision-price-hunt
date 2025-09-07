import requests
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
import logging
from datetime import datetime
from urllib.parse import urljoin, quote

from app.models.schemas import PriceInfo, ProductOffer, ProductInfo
from app.core.config import settings

logger = logging.getLogger(__name__)

class ScrapingService:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': settings.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    async def create_session(self):
        """Create aiohttp session"""
        if self.session is None:
            connector = aiohttp.TCPConnector(limit=10)
            timeout = aiohttp.ClientTimeout(total=settings.request_timeout)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.headers
            )

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    def extract_price_from_text(self, text: str) -> Optional[float]:
        """Extract price from text using regex patterns"""
        try:
            # Common price patterns for Indian currency (INR)
            patterns = [
                r'₹(\d+(?:,\d{2,3})*(?:\.\d{2})?)',  # ₹123.45, ₹1,234.56
                r'Rs\.\s*(\d+(?:,\d{2,3})*(?:\.\d{2})?)',  # Rs. 123.45
                r'Rs\s*(\d+(?:,\d{2,3})*(?:\.\d{2})?)',  # Rs 123.45
                r'(\d+(?:,\d{2,3})*(?:\.\d{2})?)\s*₹',  # 123.45₹
                r'(\d+(?:,\d{2,3})*(?:\.\d{2})?)\s*INR',  # 123.45 INR
                r'INR\s*(\d+(?:,\d{2,3})*(?:\.\d{2})?)',  # INR 123.45
                r'Price:\s*₹?(\d+(?:,\d{2,3})*(?:\.\d{2})?)',  # Price: ₹123.45
                # Fallback patterns for USD (for legacy support)
                r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $123.45, $1,234.56
                r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 123.45$
                r'USD\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # USD 123.45
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Clean and convert first match
                    price_str = matches[0].replace(',', '')
                    return float(price_str)
            
            return None
        except Exception as e:
            logger.error(f"Error extracting price: {e}")
            return None

    async def search_amazon_india(self, query: str) -> List[ProductOffer]:
        """Search Amazon India for products (mock implementation for demo)"""
        # Note: This is a simplified mock implementation
        # In production, you'd need to use Amazon's API or proper scraping
        try:
            await self.create_session()
            
            # Mock data for demo purposes with Indian pricing
            mock_offers = [
                ProductOffer(
                    product_info=ProductInfo(
                        name=f"Amazon India: {query}",
                        brand="Amazon",
                        category="Electronics",
                        description=f"Product matching {query} from Amazon India"
                    ),
                    price_info=PriceInfo(
                        price=7999.00,
                        currency="INR",
                        source="Amazon India",
                        url="https://amazon.in/product/123",
                        availability="in_stock",
                        last_updated=datetime.now()
                    ),
                    similarity_score=0.85
                )
            ]
            
            return mock_offers
            
        except Exception as e:
            logger.error(f"Error searching Amazon India: {e}")
            return []

    async def search_flipkart(self, query: str) -> List[ProductOffer]:
        """Search Flipkart for products (mock implementation)"""
        try:
            await self.create_session()
            
            # Mock data for demo purposes with Indian pricing
            mock_offers = [
                ProductOffer(
                    product_info=ProductInfo(
                        name=f"Flipkart: {query}",
                        brand="Flipkart",
                        category="Electronics",
                        description=f"Product matching {query} from Flipkart"
                    ),
                    price_info=PriceInfo(
                        price=7299.00,
                        currency="INR",
                        source="Flipkart",
                        url="https://flipkart.com/product/456",
                        availability="in_stock",
                        last_updated=datetime.now()
                    ),
                    similarity_score=0.80
                )
            ]
            
            return mock_offers
            
        except Exception as e:
            logger.error(f"Error searching Flipkart: {e}")
            return []

    async def search_indian_store(self, query: str, store_name: str = "Indian Store", base_price: float = 6999.00) -> List[ProductOffer]:
        """Search an Indian e-commerce store (mock implementation)"""
        try:
            # Mock data for demo purposes with Indian pricing
            mock_offers = [
                ProductOffer(
                    product_info=ProductInfo(
                        name=f"{store_name}: {query}",
                        brand=store_name,
                        category="General",
                        description=f"Product matching {query} from {store_name}"
                    ),
                    price_info=PriceInfo(
                        price=base_price,
                        currency="INR",
                        source=store_name,
                        url=f"https://{store_name.lower().replace(' ', '')}.com/product/789",
                        availability="in_stock",
                        last_updated=datetime.now()
                    ),
                    similarity_score=0.75
                )
            ]
            
            return mock_offers
            
        except Exception as e:
            logger.error(f"Error searching {store_name}: {e}")
            return []

    async def scrape_all_sources(self, product_info: ProductInfo) -> List[ProductOffer]:
        """Scrape all available sources for product prices"""
        all_offers = []
        
        # Create search query from product info
        search_terms = []
        if product_info.name:
            search_terms.append(product_info.name)
        if product_info.brand:
            search_terms.append(product_info.brand)
        
        query = ' '.join(search_terms).strip()
        if not query:
            query = "product"
        
        try:
            # Search multiple Indian sources concurrently
            tasks = [
                self.search_amazon_india(query),
                self.search_flipkart(query),
                self.search_indian_store(query, "Myntra", 6499.00),
                self.search_indian_store(query, "Paytm Mall", 7199.00),
                self.search_indian_store(query, "Snapdeal", 6799.00)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect all valid results
            for result in results:
                if isinstance(result, list):
                    all_offers.extend(result)
                else:
                    logger.error(f"Scraping task failed: {result}")
            
            return all_offers
            
        except Exception as e:
            logger.error(f"Error scraping all sources: {e}")
            return []
        finally:
            await self.close_session()

    def filter_and_validate_offers(self, offers: List[ProductOffer]) -> List[ProductOffer]:
        """Filter and validate scraped offers"""
        valid_offers = []
        
        for offer in offers:
            try:
                # Validate price
                if offer.price_info.price <= 0:
                    continue
                
                # Validate URL
                if not offer.price_info.url.startswith('http'):
                    continue
                
                # Validate required fields
                if not offer.product_info.name:
                    continue
                
                valid_offers.append(offer)
                
            except Exception as e:
                logger.error(f"Error validating offer: {e}")
                continue
        
        return valid_offers

# Global instance
scraping_service = ScrapingService()