from PIL import Image
from typing import Dict, List, Tuple, Optional
import re
import logging
import base64
import io

from app.models.schemas import ProductInfo
from app.core.config import settings

logger = logging.getLogger(__name__)

class VisionService:
    def __init__(self):
        logger.info("Vision service initialized (simplified version)")

    def preprocess_image(self, image_path: str) -> bool:
        """Simple image validation"""
        try:
            with Image.open(image_path) as img:
                return img.mode in ['RGB', 'RGBA', 'L']
        except Exception as e:
            logger.error(f"Error validating image: {e}")
            return False

    def extract_text_from_image(self, image_path: str) -> Tuple[str, float]:
        """Mock OCR extraction - in real implementation would use pytesseract"""
        try:
            # For demo purposes, return mock extracted text based on filename
            filename = image_path.lower()
            
            if 'iphone' in filename or 'phone' in filename:
                return "iPhone 15 Pro Max 256GB Space Black Apple", 0.95
            elif 'watch' in filename:
                return "Apple Watch Series 9 GPS 45mm Sport Band", 0.90
            elif 'laptop' in filename:
                return "MacBook Pro 14-inch M3 Pro 18GB 512GB", 0.88
            elif 'book' in filename:
                return "Python Programming Cookbook Third Edition", 0.85
            elif 'shoe' in filename:
                return "Nike Air Max 270 Running Shoes Size 10", 0.92
            else:
                return "Product Image - Brand Name Model Details", 0.75
                
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return "Unknown Product", 0.0

    def extract_product_info(self, extracted_text: str) -> Dict[str, str]:
        """Extract structured product information from text"""
        product_info = {
            "name": "",
            "brand": "",
            "category": "",
            "description": ""
        }
        
        try:
            text = re.sub(r'\s+', ' ', extracted_text).strip()
            
            # Brand detection patterns
            brand_patterns = [
                r'\b(Apple|Samsung|Sony|Nike|Adidas|Dell|HP|Lenovo)\b',
                r'\b(Microsoft|Google|Amazon|Canon|Nikon|ASUS)\b'
            ]
            
            for pattern in brand_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    product_info["brand"] = match.group(1)
                    break
            
            # Category detection
            category_keywords = {
                "Electronics": ["iphone", "phone", "laptop", "macbook", "watch", "ipad"],
                "Clothing": ["shirt", "pants", "dress", "jacket"],
                "Footwear": ["shoes", "sneakers", "boots", "nike", "adidas"],
                "Books": ["book", "cookbook", "programming", "edition"]
            }
            
            text_lower = text.lower()
            for category, keywords in category_keywords.items():
                if any(keyword in text_lower for keyword in keywords):
                    product_info["category"] = category
                    break
            
            # Use first few words as product name
            words = text.split()
            if words:
                product_info["name"] = ' '.join(words[:6])
            
            product_info["description"] = text
            
        except Exception as e:
            logger.error(f"Error extracting product info: {e}")
        
        return product_info

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Simple string-based similarity"""
        try:
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0

    async def analyze_product_image(self, image_path: str) -> ProductInfo:
        """Main method to analyze product image and extract information"""
        try:
            # Validate image
            if not self.preprocess_image(image_path):
                raise ValueError("Invalid image file")
            
            # Extract text from image (mock)
            extracted_text, confidence = self.extract_text_from_image(image_path)
            
            # Extract structured product information
            product_data = self.extract_product_info(extracted_text)
            
            # Create ProductInfo object
            product_info = ProductInfo(
                name=product_data["name"] or "Unknown Product",
                brand=product_data["brand"] or None,
                category=product_data["category"] or None,
                description=product_data["description"] or None,
                extracted_text=extracted_text,
                confidence=confidence
            )
            
            return product_info
            
        except Exception as e:
            logger.error(f"Error analyzing product image: {e}")
            return ProductInfo(
                name="Unknown Product",
                extracted_text="",
                confidence=0.0
            )

# Global instance
vision_service = VisionService()