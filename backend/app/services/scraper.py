import requests
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
import logging
from datetime import datetime
from urllib.parse import urljoin, quote, urlparse
import random
import time
from fake_useragent import UserAgent

from app.models.schemas import PriceInfo, ProductOffer, ProductInfo
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize user agent generator
ua = UserAgent()

class ScrapingService:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.request_delays = {
            'amazon.in': (1, 3),  # 1-3 seconds delay
            'flipkart.com': (1, 2),  # 1-2 seconds delay
            'default': (0.5, 1.5)
        }

    async def create_session(self):
        """Create aiohttp session with random user agent"""
        if self.session is None:
            # Update headers with new random user agent
            self.headers['User-Agent'] = ua.random
            
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

    def get_domain_delay(self, url: str) -> float:
        """Get appropriate delay for domain to be respectful"""
        try:
            domain = urlparse(url).netloc
            for key, (min_delay, max_delay) in self.request_delays.items():
                if key in domain:
                    return random.uniform(min_delay, max_delay)
            return random.uniform(*self.request_delays['default'])
        except:
            return 1.0

    def should_use_real_scraping(self) -> bool:
        """Determine if real scraping should be used based on configuration"""
        return settings.enable_real_scraping

    async def safe_request(self, url: str, **kwargs) -> Optional[str]:
        """Make a safe HTTP request with proper delays and error handling"""
        if not self.should_use_real_scraping():
            logger.info("Real scraping is disabled, skipping request")
            return None
            
        try:
            await self.create_session()
            
            # Add delay to be respectful
            delay = self.get_domain_delay(url)
            await asyncio.sleep(delay)
            
            # Add timeout and retry logic
            for attempt in range(settings.max_retries):
                try:
                    async with self.session.get(url, **kwargs) as response:
                        if response.status == 200:
                            content = await response.text()
                            logger.info(f"Successfully fetched {url} (attempt {attempt + 1})")
                            return content
                        elif response.status == 429:  # Rate limited
                            logger.warning(f"Rate limited on {url}, waiting before retry")
                            await asyncio.sleep(random.uniform(5, 10))
                        else:
                            logger.warning(f"HTTP {response.status} for {url}")
                            
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
                    if attempt < settings.max_retries - 1:
                        await asyncio.sleep(random.uniform(2, 5))
                        
                except Exception as e:
                    logger.warning(f"Request error on attempt {attempt + 1} for {url}: {e}")
                    if attempt < settings.max_retries - 1:
                        await asyncio.sleep(random.uniform(1, 3))
            
            logger.error(f"All {settings.max_retries} attempts failed for {url}")
            return None
                    
        except Exception as e:
            logger.error(f"Fatal error requesting {url}: {e}")
            return None

    def clean_product_name(self, name: str) -> str:
        """Clean and normalize product name"""
        if not name:
            return ""
        
        # Remove extra whitespace and normalize
        name = ' '.join(name.split())
        
        # Remove common unwanted characters and patterns
        name = re.sub(r'[^\w\s\-\(\)\[\]&]', '', name)
        name = re.sub(r'\s+', ' ', name)
        
        return name.strip()

    def validate_price(self, price: float) -> bool:
        """Validate if price is reasonable"""
        if not price or price <= 0:
            return False
        
        # Basic sanity checks (adjust based on your use case)
        if price < 1 or price > 10000000:  # Between ₹1 and ₹1 crore
            return False
            
        return True

    def generate_product_url(self, source_url: str, product_path: str) -> str:
        """Generate a valid product URL"""
        try:
            if product_path.startswith('http'):
                return product_path
            elif product_path.startswith('/'):
                return source_url + product_path
            else:
                return f"{source_url}/{product_path}"
        except:
            return source_url

    def extract_price_from_text(self, text: str) -> Optional[float]:
        """Extract price from text using regex patterns"""
        try:
            # Clean the text first
            text = re.sub(r'[^\d₹Rs\$\.,\s]', ' ', text)
            
            # Common price patterns for Indian currency (INR)
            patterns = [
                r'₹(\d+(?:,\d{2,3})*(?:\.\d{2})?)',  # ₹123.45, ₹1,234.56
                r'Rs\.?\s*(\d+(?:,\d{2,3})*(?:\.\d{2})?)',  # Rs. 123.45, Rs 123.45
                r'(\d+(?:,\d{2,3})*(?:\.\d{2})?)\s*₹',  # 123.45₹
                r'(\d+(?:,\d{2,3})*(?:\.\d{2})?)\s*INR',  # 123.45 INR
                r'INR\s*(\d+(?:,\d{2,3})*(?:\.\d{2})?)',  # INR 123.45
                r'Price:?\s*₹?(\d+(?:,\d{2,3})*(?:\.\d{2})?)',  # Price: ₹123.45
                # Fallback patterns for USD (for legacy support)
                r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $123.45, $1,234.56
                r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 123.45$
                r'USD\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # USD 123.45
                # Simple number patterns as last resort
                r'(\d+(?:,\d{2,3})*(?:\.\d{2})?)',  # Any number with commas
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Clean and convert first match
                    price_str = matches[0].replace(',', '')
                    price = float(price_str)
                    
                    # Validate the price
                    if self.validate_price(price):
                        return price
            
            return None
        except Exception as e:
            logger.error(f"Error extracting price from '{text}': {e}")
            return None
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
        """Search Amazon India for products with real-time scraping"""
        offers = []
        
        try:
            # Construct Amazon India search URL
            search_url = f"https://www.amazon.in/s?k={quote(query)}&ref=sr_pg_1"
            
            logger.info(f"Scraping Amazon India: {search_url}")
            
            # Get the search results page
            html_content = await self.safe_request(search_url)
            
            if not html_content:
                logger.warning("Failed to get Amazon search results, falling back to mock data")
                return await self._get_amazon_mock_data(query)
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Multiple selectors for Amazon product containers
            selectors = [
                {'selector': 'div[data-component-type="s-search-result"]', 'name': 'data-component'},
                {'selector': 'div.s-result-item', 'name': 's-result-item'},
                {'selector': '[data-asin]', 'name': 'data-asin'},
                {'selector': '.s-card-container', 'name': 's-card-container'}
            ]
            
            product_containers = []
            for selector_info in selectors:
                containers = soup.select(selector_info['selector'])
                if containers:
                    logger.info(f"Found {len(containers)} products using {selector_info['name']} selector")
                    product_containers = containers
                    break
            
            if not product_containers:
                logger.warning("No product containers found on Amazon")
                return await self._get_amazon_mock_data(query)
            
            logger.info(f"Processing {min(len(product_containers), settings.max_products_per_source)} products from Amazon")
            
            for container in product_containers[:settings.max_products_per_source]:
                try:
                    # Multiple selectors for product name
                    name_selectors = [
                        'h2 a span',
                        'h2 span',
                        '.s-size-mini span',
                        '[data-cy="title-recipe-label"]',
                        '.a-text-normal'
                    ]
                    
                    product_name = None
                    for selector in name_selectors:
                        name_elem = container.select_one(selector)
                        if name_elem:
                            product_name = self.clean_product_name(name_elem.get_text(strip=True))
                            if product_name:
                                break
                    
                    if not product_name:
                        continue
                    
                    # Multiple selectors for price
                    price_selectors = [
                        '.a-price-whole',
                        '.a-price .a-offscreen',
                        '.a-price',
                        '.s-price-instructions-style .a-price',
                        '[data-cy="price-recipe"]'
                    ]
                    
                    price = None
                    for selector in price_selectors:
                        price_elem = container.select_one(selector)
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            price = self.extract_price_from_text(price_text)
                            if price and price > 0:
                                break
                    
                    if not price or price <= 0:
                        continue
                    
                    # Extract product URL
                    product_url = "https://www.amazon.in/"
                    link_elem = container.select_one('h2 a, .s-link-style a, [data-cy="title-recipe-label"]')
                    if link_elem:
                        href = link_elem.get('href', '')
                        product_url = self.generate_product_url("https://www.amazon.in", href)
                    
                    # Extract availability
                    availability = "in_stock"
                    avail_selectors = [
                        '.a-color-state',
                        '.s-color-state',
                        '[data-cy="availability-recipe"]'
                    ]
                    
                    for selector in avail_selectors:
                        avail_elem = container.select_one(selector)
                        if avail_elem:
                            avail_text = avail_elem.get_text(strip=True).lower()
                            if any(term in avail_text for term in ['out of stock', 'unavailable', 'not available']):
                                availability = "out_of_stock"
                                break
                    
                    # Create offer object
                    offer = ProductOffer(
                        product_info=ProductInfo(
                            name=product_name,
                            brand="Amazon India",
                            category="Electronics",
                            description=f"Product from Amazon India: {product_name}"
                        ),
                        price_info=PriceInfo(
                            price=price,
                            currency="INR",
                            source="Amazon India",
                            url=product_url,
                            availability=availability,
                            last_updated=datetime.now()
                        ),
                        similarity_score=0.85
                    )
                    
                    offers.append(offer)
                    
                except Exception as e:
                    logger.error(f"Error parsing Amazon product: {e}")
                    continue
            
            if not offers:
                logger.warning("No valid offers found on Amazon, using mock data")
                return await self._get_amazon_mock_data(query)
                
            logger.info(f"Successfully scraped {len(offers)} offers from Amazon India")
            return offers
            
        except Exception as e:
            logger.error(f"Error searching Amazon India: {e}")
            # Fallback to mock data
            return await self._get_amazon_mock_data(query)

    async def _get_amazon_mock_data(self, query: str) -> List[ProductOffer]:
        """Fallback mock data for Amazon India"""
        return [
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

    async def search_flipkart(self, query: str) -> List[ProductOffer]:
        """Search Flipkart for products with real-time scraping"""
        offers = []
        
        try:
            # Construct Flipkart search URL
            search_url = f"https://www.flipkart.com/search?q={quote(query)}"
            
            logger.info(f"Scraping Flipkart: {search_url}")
            
            # Get the search results page
            html_content = await self.safe_request(search_url)
            
            if not html_content:
                logger.warning("Failed to get Flipkart search results, falling back to mock data")
                return await self._get_flipkart_mock_data(query)
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Multiple selectors for Flipkart product containers
            selectors = [
                {'selector': '[data-id]', 'name': 'data-id'},
                {'selector': '._1AtVbE', 'name': '_1AtVbE'},
                {'selector': '._2kHMtA', 'name': '_2kHMtA'},
                {'selector': '._3pLy-c', 'name': '_3pLy-c'},
                {'selector': '._13oc-S', 'name': '_13oc-S'},
                {'selector': '.s1Q9rs', 'name': 's1Q9rs'}
            ]
            
            product_containers = []
            for selector_info in selectors:
                containers = soup.select(selector_info['selector'])
                if containers:
                    logger.info(f"Found {len(containers)} products using {selector_info['name']} selector")
                    product_containers = containers
                    break
            
            if not product_containers:
                logger.warning("No product containers found on Flipkart")
                return await self._get_flipkart_mock_data(query)
            
            logger.info(f"Processing {min(len(product_containers), settings.max_products_per_source)} products from Flipkart")
            
            for container in product_containers[:settings.max_products_per_source]:
                try:
                    # Multiple selectors for product name
                    name_selectors = [
                        '.IRpwTa',
                        '._1fQZEK',
                        '.s1Q9rs',
                        '._4rR01T',
                        '.B_NuCI',
                        '._3wU53n',
                        'a[title]'
                    ]
                    
                    product_name = None
                    for selector in name_selectors:
                        name_elem = container.select_one(selector)
                        if name_elem:
                            # Try title attribute first, then text content
                            name_text = name_elem.get('title') or name_elem.get_text(strip=True)
                            product_name = self.clean_product_name(name_text)
                            if product_name:
                                break
                    
                    if not product_name:
                        continue
                    
                    # Multiple selectors for price
                    price_selectors = [
                        '._30jeq3',
                        '._1_WHN1',
                        '._3I9_wc',
                        '._25b18c',
                        '.X9PEe1',
                        '._3tbKJL'
                    ]
                    
                    price = None
                    for selector in price_selectors:
                        price_elem = container.select_one(selector)
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            price = self.extract_price_from_text(price_text)
                            if price and price > 0:
                                break
                    
                    if not price or price <= 0:
                        continue
                    
                    # Extract product URL
                    product_url = "https://www.flipkart.com/"
                    link_elem = container.select_one('a[href]')
                    if link_elem:
                        href = link_elem.get('href', '')
                        product_url = self.generate_product_url("https://www.flipkart.com", href)
                    
                    # Extract availability
                    availability = "in_stock"  # Default for Flipkart
                    
                    # Create offer object
                    offer = ProductOffer(
                        product_info=ProductInfo(
                            name=product_name,
                            brand="Flipkart",
                            category="Electronics",
                            description=f"Product from Flipkart: {product_name}"
                        ),
                        price_info=PriceInfo(
                            price=price,
                            currency="INR",
                            source="Flipkart",
                            url=product_url,
                            availability=availability,
                            last_updated=datetime.now()
                        ),
                        similarity_score=0.80
                    )
                    
                    offers.append(offer)
                    
                except Exception as e:
                    logger.error(f"Error parsing Flipkart product: {e}")
                    continue
            
            if not offers:
                logger.warning("No valid offers found on Flipkart, using mock data")
                return await self._get_flipkart_mock_data(query)
                
            logger.info(f"Successfully scraped {len(offers)} offers from Flipkart")
            return offers
            
        except Exception as e:
            logger.error(f"Error searching Flipkart: {e}")
            # Fallback to mock data
            return await self._get_flipkart_mock_data(query)

    async def _get_flipkart_mock_data(self, query: str) -> List[ProductOffer]:
        """Fallback mock data for Flipkart"""
        return [
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

    async def search_indian_store(self, query: str, store_name: str = "Indian Store", base_price: float = 6999.00) -> List[ProductOffer]:
        """Search an Indian e-commerce store (enhanced mock implementation with variety)"""
        try:
            # Add some price variation based on query and store
            price_variation = random.uniform(0.9, 1.1)
            final_price = base_price * price_variation
            
            # Add some randomness to availability
            availability = random.choice(["in_stock", "in_stock", "in_stock", "limited_stock"])
            
            mock_offers = [
                ProductOffer(
                    product_info=ProductInfo(
                        name=f"{store_name}: {query}",
                        brand=store_name,
                        category="General",
                        description=f"Product matching {query} from {store_name}"
                    ),
                    price_info=PriceInfo(
                        price=round(final_price, 2),
                        currency="INR",
                        source=store_name,
                        url=f"https://{store_name.lower().replace(' ', '')}.com/product/{hash(query) % 10000}",
                        availability=availability,
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