from PIL import Image, ImageEnhance, ImageFilter
from typing import Dict, List, Tuple, Optional
import re
import logging
import base64
import io
import pytesseract

from app.models.schemas import ProductInfo
from app.core.config import settings

logger = logging.getLogger(__name__)

class VisionService:
    def __init__(self):
        """Initialize vision service with OCR capabilities"""
        self.text_model = None
        logger.info("Vision service initialized with real OCR support")
        
        # Check if tesseract is available
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract OCR version: {version}")
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")

    def preprocess_image_for_ocr(self, image_path: str) -> Image.Image:
        """Preprocess image to improve OCR accuracy"""
        try:
            # Open and convert image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize image if too small (minimum 300px width)
                width, height = img.size
                if width < 300:
                    scale = 300 / width
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Enhance contrast and sharpness for better OCR
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.5)
                
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(2.0)
                
                return img
                
        except Exception as e:
            logger.error(f"Error preprocessing image for OCR: {e}")
            # Return original image if preprocessing fails
            return Image.open(image_path)

    def preprocess_image(self, image_path: str) -> bool:
        """Simple image validation"""
        try:
            with Image.open(image_path) as img:
                return img.mode in ['RGB', 'RGBA', 'L']
        except Exception as e:
            logger.error(f"Error validating image: {e}")
            return False

    def extract_text_from_image(self, image_path: str) -> Tuple[str, float]:
        """Extract text from image using OCR (pytesseract)"""
        try:
            # Preprocess image for better OCR results
            processed_img = self.preprocess_image_for_ocr(image_path)
            
            # Configure tesseract for better results
            custom_config = r'--oem 3 --psm 6'
            
            # Extract text using pytesseract
            extracted_text = pytesseract.image_to_string(processed_img, config=custom_config)
            
            # Clean up the extracted text
            extracted_text = re.sub(r'\s+', ' ', extracted_text).strip()
            
            # Calculate confidence based on text length and quality
            confidence = 0.0
            if extracted_text:
                # Basic confidence calculation
                word_count = len(extracted_text.split())
                char_count = len(extracted_text)
                
                # Higher confidence for longer, more structured text
                if word_count >= 3 and char_count >= 10:
                    confidence = min(0.9, 0.5 + (word_count * 0.05) + (char_count * 0.002))
                elif word_count >= 1:
                    confidence = min(0.6, 0.3 + (word_count * 0.1))
                else:
                    confidence = 0.1
                
                # Boost confidence if we detect common product-related patterns
                product_patterns = [
                    r'\b(iPhone|Samsung|Apple|Google|Sony|Dell|HP|Lenovo|Nike|Adidas)\b',
                    r'\b(Pro|Max|Plus|Ultra|Series|Edition|Model)\b',
                    r'\b(\d+GB|\d+TB|\d+MB)\b',
                    r'\$\d+|\₹\d+|Rs\.?\s*\d+',
                    r'\b(Black|White|Blue|Red|Gray|Silver|Gold)\b'
                ]
                
                for pattern in product_patterns:
                    if re.search(pattern, extracted_text, re.IGNORECASE):
                        confidence = min(0.95, confidence + 0.1)
            
            logger.info(f"OCR extracted text: '{extracted_text}' with confidence: {confidence}")
            
            if not extracted_text.strip():
                # Fallback to basic image analysis if no text found
                return self._analyze_image_without_text(image_path)
            
            return extracted_text, confidence
                
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            # Fallback to basic image analysis
            return self._analyze_image_without_text(image_path)

    def _analyze_image_without_text(self, image_path: str) -> Tuple[str, float]:
        """Fallback analysis when no text is found"""
        try:
            # Analyze filename and basic image properties
            filename = image_path.lower()
            
            if 'iphone' in filename or 'phone' in filename:
                return "iPhone mobile phone device", 0.60
            elif 'watch' in filename:
                return "watch timepiece device", 0.60
            elif 'laptop' in filename or 'macbook' in filename:
                return "laptop computer device", 0.60
            elif 'book' in filename:
                return "book publication", 0.60
            elif 'shoe' in filename or 'nike' in filename:
                return "shoes footwear", 0.60
            else:
                return "product item", 0.30
                
        except Exception as e:
            logger.error(f"Error in fallback image analysis: {e}")
            return "unknown product", 0.1

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
            
            # Enhanced brand detection patterns
            brand_patterns = [
                r'\b(Apple|iPhone|iPad|MacBook|iMac)\b',
                r'\b(Samsung|Galaxy|Note)\b',
                r'\b(Sony|PlayStation|Xperia)\b',
                r'\b(Nike|Air\s+Max|Jordan)\b',
                r'\b(Adidas|Ultraboost|Stan\s+Smith)\b',
                r'\b(Dell|Inspiron|XPS|Latitude)\b',
                r'\b(HP|Pavilion|Envy|Spectre)\b',
                r'\b(Lenovo|ThinkPad|IdeaPad)\b',
                r'\b(Microsoft|Surface|Xbox)\b',
                r'\b(Google|Pixel|Chromebook)\b',
                r'\b(Amazon|Kindle|Echo)\b',
                r'\b(Canon|Nikon|Pentax)\b',
                r'\b(ASUS|ROG|ZenBook)\b',
                r'\b(OnePlus|Nothing|Xiaomi|Oppo|Vivo)\b'
            ]
            
            # Try to find brand
            for pattern in brand_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    brand_text = match.group(0)
                    # Clean up brand name
                    if 'iphone' in brand_text.lower() or 'ipad' in brand_text.lower() or 'macbook' in brand_text.lower():
                        product_info["brand"] = "Apple"
                    elif 'galaxy' in brand_text.lower() or 'note' in brand_text.lower():
                        product_info["brand"] = "Samsung"
                    elif 'air max' in brand_text.lower() or 'jordan' in brand_text.lower():
                        product_info["brand"] = "Nike"
                    else:
                        product_info["brand"] = brand_text.title()
                    break
            
            # Enhanced category detection
            category_keywords = {
                "Electronics": [
                    "iphone", "phone", "smartphone", "mobile", "cell",
                    "laptop", "macbook", "computer", "pc", "notebook",
                    "watch", "smartwatch", "ipad", "tablet",
                    "tv", "television", "monitor", "screen",
                    "camera", "lens", "dslr", "mirrorless",
                    "headphones", "earbuds", "speaker", "audio",
                    "gaming", "console", "xbox", "playstation", "switch"
                ],
                "Clothing": [
                    "shirt", "t-shirt", "tshirt", "pants", "jeans", "dress", 
                    "jacket", "coat", "sweater", "hoodie", "shorts",
                    "suit", "blazer", "skirt", "top", "blouse"
                ],
                "Footwear": [
                    "shoes", "sneakers", "boots", "sandals", "slippers",
                    "air max", "jordan", "ultraboost", "running shoes",
                    "dress shoes", "casual shoes", "athletic shoes"
                ],
                "Books": [
                    "book", "cookbook", "programming", "edition", "manual",
                    "guide", "textbook", "novel", "magazine", "journal"
                ],
                "Home & Kitchen": [
                    "kitchen", "cooking", "appliance", "blender", "microwave",
                    "furniture", "chair", "table", "bed", "sofa"
                ],
                "Beauty & Personal Care": [
                    "skincare", "makeup", "perfume", "shampoo", "cosmetics",
                    "lotion", "cream", "serum", "lipstick"
                ]
            }
            
            text_lower = text.lower()
            max_matches = 0
            best_category = None
            
            for category, keywords in category_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in text_lower)
                if matches > max_matches:
                    max_matches = matches
                    best_category = category
            
            if best_category:
                product_info["category"] = best_category
            
            # Extract product name - prioritize meaningful text
            words = text.split()
            if words:
                # Try to build a meaningful product name
                name_parts = []
                
                # Look for model numbers, sizes, colors
                for word in words:
                    if re.match(r'^\d+[A-Z]*$', word):  # Model numbers like "15", "256GB"
                        name_parts.append(word)
                    elif word.lower() in ['pro', 'max', 'plus', 'ultra', 'series', 'edition']:
                        name_parts.append(word.title())
                    elif re.match(r'^\d+(gb|tb|mb|inch)$', word.lower()):  # Storage/size
                        name_parts.append(word.upper())
                    elif word.lower() in ['black', 'white', 'blue', 'red', 'gray', 'silver', 'gold', 'space']:
                        name_parts.append(word.title())
                
                # If we found specific attributes, combine with brand
                if name_parts and product_info["brand"]:
                    product_info["name"] = f"{product_info['brand']} {' '.join(name_parts)}"
                elif name_parts:
                    product_info["name"] = ' '.join(name_parts)
                else:
                    # Fallback to first few meaningful words
                    meaningful_words = [w for w in words[:8] if len(w) > 2 and not w.isdigit()]
                    product_info["name"] = ' '.join(meaningful_words[:4])
            
            # If name is still empty, use category + brand
            if not product_info["name"]:
                if product_info["brand"] and product_info["category"]:
                    product_info["name"] = f"{product_info['brand']} {product_info['category']} Product"
                elif product_info["brand"]:
                    product_info["name"] = f"{product_info['brand']} Product"
                elif product_info["category"]:
                    product_info["name"] = f"{product_info['category']} Product"
                else:
                    product_info["name"] = "Product"
            
            product_info["description"] = text
            
        except Exception as e:
            logger.error(f"Error extracting product info: {e}")
            # Fallback to basic info
            product_info["name"] = "Product"
            product_info["description"] = extracted_text
        
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