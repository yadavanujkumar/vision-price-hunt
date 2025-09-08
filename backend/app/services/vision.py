from PIL import Image, ImageEnhance, ImageFilter
from typing import Dict, List, Tuple, Optional
import re
import logging
import base64
import io
import pytesseract
import cv2
import numpy as np
from collections import Counter

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
        """Enhanced analysis when no text is found using computer vision"""
        try:
            # First try visual analysis
            visual_result = self._analyze_visual_features(image_path)
            if visual_result:
                return visual_result
            
            # Fallback to filename analysis
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

    def _analyze_visual_features(self, image_path: str) -> Optional[Tuple[str, float]]:
        """Analyze visual features of the image to identify product"""
        try:
            # Load image with OpenCV
            image = cv2.imread(image_path)
            if image is None:
                logger.warning(f"Could not load image: {image_path}")
                return None
            
            # Convert to RGB for analysis
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Analyze different visual aspects
            color_analysis = self._analyze_color_distribution(image_rgb)
            shape_analysis = self._analyze_shapes_and_contours(image)
            size_analysis = self._analyze_image_dimensions(image)
            
            # Combine analyses to determine product type
            product_info = self._classify_product_from_visual_features(
                color_analysis, shape_analysis, size_analysis
            )
            
            return product_info
            
        except Exception as e:
            logger.error(f"Error in visual feature analysis: {e}")
            return None

    def _analyze_color_distribution(self, image_rgb: np.ndarray) -> Dict:
        """Analyze color distribution and dominant colors"""
        try:
            # Resize image for faster processing
            height, width = image_rgb.shape[:2]
            if width > 300:
                scale = 300 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                image_rgb = cv2.resize(image_rgb, (new_width, new_height))
            
            # Flatten the image and get dominant colors
            pixels = image_rgb.reshape(-1, 3)
            
            # K-means clustering to find dominant colors
            from sklearn.cluster import KMeans
            try:
                kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
                kmeans.fit(pixels)
                colors = kmeans.cluster_centers_.astype(int)
                
                # Count frequency of each cluster
                labels = kmeans.labels_
                label_counts = Counter(labels)
                
                dominant_colors = []
                for label, count in label_counts.most_common(3):
                    color = colors[label]
                    dominant_colors.append({
                        'rgb': color.tolist(),
                        'percentage': count / len(labels) * 100
                    })
                
            except ImportError:
                # Fallback without sklearn
                dominant_colors = self._get_dominant_colors_simple(pixels)
            
            return {
                'dominant_colors': dominant_colors,
                'is_monochrome': self._is_monochrome(image_rgb),
                'has_metallic_appearance': self._detect_metallic_appearance(dominant_colors)
            }
            
        except Exception as e:
            logger.error(f"Error in color analysis: {e}")
            return {'dominant_colors': [], 'is_monochrome': False, 'has_metallic_appearance': False}

    def _get_dominant_colors_simple(self, pixels: np.ndarray) -> List[Dict]:
        """Simple dominant color extraction without sklearn"""
        # Quantize colors to reduce complexity
        quantized = (pixels // 32) * 32
        
        # Count unique colors
        unique_colors, counts = np.unique(quantized.reshape(-1, 3), axis=0, return_counts=True)
        
        # Get top 3 colors
        top_indices = np.argsort(counts)[-3:][::-1]
        
        dominant_colors = []
        total_pixels = len(pixels)
        
        for idx in top_indices:
            color = unique_colors[idx]
            count = counts[idx]
            dominant_colors.append({
                'rgb': color.tolist(),
                'percentage': count / total_pixels * 100
            })
        
        return dominant_colors

    def _is_monochrome(self, image_rgb: np.ndarray) -> bool:
        """Check if image is predominantly monochrome"""
        try:
            # Convert to grayscale and check color variance
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            color_variance = np.var(image_rgb, axis=(0, 1))
            
            # If color variance is low, it's likely monochrome
            return np.mean(color_variance) < 100
            
        except Exception:
            return False

    def _detect_metallic_appearance(self, dominant_colors: List[Dict]) -> bool:
        """Detect if the image has metallic/shiny appearance"""
        try:
            metallic_colors = [
                [169, 169, 169],  # Silver
                [192, 192, 192],  # Light gray
                [128, 128, 128],  # Gray
                [255, 215, 0],    # Gold
                [184, 134, 11],   # Dark goldenrod
                [105, 105, 105],  # Dim gray
            ]
            
            for color_info in dominant_colors:
                rgb = color_info['rgb']
                for metallic in metallic_colors:
                    # Calculate color distance
                    distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(rgb, metallic)))
                    if distance < 50 and color_info['percentage'] > 15:
                        return True
            
            return False
            
        except Exception:
            return False

    def _analyze_shapes_and_contours(self, image: np.ndarray) -> Dict:
        """Analyze shapes and contours in the image"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return {'shapes': [], 'has_rectangular_objects': False, 'has_circular_objects': False}
            
            # Analyze shapes
            shapes = []
            rectangular_count = 0
            circular_count = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 500:  # Skip small contours
                    continue
                
                # Approximate contour
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Classify shape based on number of vertices
                vertices = len(approx)
                
                if vertices == 4:
                    # Check if it's rectangular
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    shapes.append({
                        'type': 'rectangular',
                        'area': area,
                        'aspect_ratio': aspect_ratio
                    })
                    rectangular_count += 1
                    
                elif vertices > 8:
                    # Likely circular
                    # Check circularity
                    perimeter = cv2.arcLength(contour, True)
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    
                    if circularity > 0.7:
                        shapes.append({
                            'type': 'circular',
                            'area': area,
                            'circularity': circularity
                        })
                        circular_count += 1
            
            return {
                'shapes': shapes,
                'has_rectangular_objects': rectangular_count > 0,
                'has_circular_objects': circular_count > 0,
                'dominant_shape': 'rectangular' if rectangular_count > circular_count else 'circular' if circular_count > 0 else 'irregular'
            }
            
        except Exception as e:
            logger.error(f"Error in shape analysis: {e}")
            return {'shapes': [], 'has_rectangular_objects': False, 'has_circular_objects': False}

    def _analyze_image_dimensions(self, image: np.ndarray) -> Dict:
        """Analyze image dimensions and aspect ratio"""
        try:
            height, width = image.shape[:2]
            aspect_ratio = width / height
            
            # Classify aspect ratio
            if 0.9 <= aspect_ratio <= 1.1:
                ratio_type = 'square'
            elif aspect_ratio > 1.5:
                ratio_type = 'wide'
            elif aspect_ratio < 0.7:
                ratio_type = 'tall'
            else:
                ratio_type = 'standard'
            
            return {
                'width': width,
                'height': height,
                'aspect_ratio': aspect_ratio,
                'ratio_type': ratio_type
            }
            
        except Exception as e:
            logger.error(f"Error in dimension analysis: {e}")
            return {'aspect_ratio': 1.0, 'ratio_type': 'standard'}

    def _classify_product_from_visual_features(self, color_analysis: Dict, shape_analysis: Dict, size_analysis: Dict) -> Tuple[str, float]:
        """Classify product type based on visual features"""
        try:
            confidence = 0.45  # Base confidence for visual analysis
            product_type = "product"
            category = "unknown"
            descriptors = []
            
            # Analyze colors for product hints
            dominant_colors = color_analysis.get('dominant_colors', [])
            is_metallic = color_analysis.get('has_metallic_appearance', False)
            is_monochrome = color_analysis.get('is_monochrome', False)
            
            # Get aspect ratio
            aspect_ratio = size_analysis.get('aspect_ratio', 1.0)
            ratio_type = size_analysis.get('ratio_type', 'standard')
            
            # Electronics detection based on metallic appearance and aspect ratio
            if is_metallic or is_monochrome:
                # Laptop detection: wide aspect ratio + metallic
                if 1.3 <= aspect_ratio <= 2.0:
                    product_type = "laptop computer"
                    category = "Electronics"
                    confidence += 0.25
                # Phone detection: tall aspect ratio 
                elif 0.4 <= aspect_ratio <= 0.8:
                    product_type = "smartphone mobile phone"
                    category = "Electronics"
                    confidence += 0.25
                # Tablet detection: slightly wide but not laptop-wide
                elif 1.1 <= aspect_ratio <= 1.4:
                    product_type = "tablet device"
                    category = "Electronics"
                    confidence += 0.2
                # Watch detection: square-ish aspect ratio
                elif 0.8 <= aspect_ratio <= 1.2:
                    product_type = "watch timepiece"
                    category = "Electronics"
                    confidence += 0.2
                else:
                    product_type = "electronic device"
                    category = "Electronics"
                    confidence += 0.15
            
            # Footwear detection: dark colors + standard/wide ratio
            elif self._has_dark_colors(dominant_colors):
                if ratio_type in ['standard', 'wide']:
                    product_type = "shoes footwear"
                    category = "Footwear"
                    confidence += 0.2
                elif ratio_type == 'tall':
                    # Dark + tall could be a phone
                    product_type = "smartphone mobile phone"
                    category = "Electronics"
                    confidence += 0.15
            
            # Books detection: rectangular + light colors (paper-like)
            elif self._has_light_colors(dominant_colors):
                if ratio_type in ['tall', 'standard']:
                    product_type = "book publication"
                    category = "Books"
                    confidence += 0.15
            
            # Clothing detection: mixed colors, non-metallic
            elif len(dominant_colors) >= 2 and not is_metallic:
                product_type = "clothing apparel"
                category = "Clothing"
                confidence += 0.15
            
            # Add descriptive elements
            if is_metallic:
                descriptors.append("metallic")
            
            if is_monochrome:
                descriptors.append("monochrome")
            
            # Add aspect ratio descriptor
            if ratio_type == 'wide':
                descriptors.append("wide")
            elif ratio_type == 'tall':
                descriptors.append("tall")
            elif ratio_type == 'square':
                descriptors.append("square")
            
            # Build final description
            if descriptors:
                description = f"{' '.join(descriptors)} {product_type}"
            else:
                description = product_type
            
            # Cap confidence but ensure it's reasonable for visual analysis
            confidence = min(confidence, 0.75)
            confidence = max(confidence, 0.35)  # Minimum confidence for visual analysis
            
            logger.info(f"Visual classification: {description} (confidence: {confidence:.2f})")
            
            return description, confidence
            
        except Exception as e:
            logger.error(f"Error in product classification: {e}")
            return "product item", 0.35

    def _has_dark_colors(self, dominant_colors: List[Dict]) -> bool:
        """Check if image has predominantly dark colors"""
        try:
            dark_color_percentage = 0
            for color_info in dominant_colors[:2]:  # Check top 2 colors
                rgb = color_info['rgb']
                brightness = sum(rgb) / 3
                if brightness < 100:  # Dark color threshold
                    dark_color_percentage += color_info['percentage']
            
            return dark_color_percentage > 30
        except Exception:
            return False

    def _has_light_colors(self, dominant_colors: List[Dict]) -> bool:
        """Check if image has predominantly light colors (paper-like)"""
        try:
            light_color_percentage = 0
            for color_info in dominant_colors[:2]:  # Check top 2 colors
                rgb = color_info['rgb']
                brightness = sum(rgb) / 3
                if brightness > 180:  # Light color threshold
                    light_color_percentage += color_info['percentage']
            
            return light_color_percentage > 40
        except Exception:
            return False

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
            
            # Extract text from image
            extracted_text, ocr_confidence = self.extract_text_from_image(image_path)
            
            # Initialize variables for final decision
            final_name = "Unknown Product"
            final_brand = None
            final_category = None
            final_description = None
            final_confidence = 0.0
            
            # Check if we have meaningful text (more than just noise)
            meaningful_text = self._has_meaningful_text(extracted_text)
            
            if meaningful_text and ocr_confidence > 0.5:
                # Use text-based analysis for high-confidence OCR results
                logger.info(f"Using text-based analysis (OCR confidence: {ocr_confidence:.2f})")
                product_data = self.extract_product_info(extracted_text)
                
                final_name = product_data["name"] or "Product"
                final_brand = product_data["brand"] or None
                final_category = product_data["category"] or None
                final_description = product_data["description"] or extracted_text
                final_confidence = ocr_confidence
                
            else:
                # Use visual analysis for low-confidence OCR or meaningless text
                logger.info(f"Using visual analysis (OCR confidence too low: {ocr_confidence:.2f} or text not meaningful)")
                
                # Get visual analysis result
                visual_result = self._analyze_visual_features(image_path)
                
                if visual_result:
                    visual_description, visual_confidence = visual_result
                    
                    # Parse the visual description to extract components
                    visual_parts = visual_description.split()
                    
                    # Try to extract category and product type from visual description
                    if 'laptop' in visual_description:
                        final_category = "Electronics"
                        final_name = "Laptop Computer"
                    elif 'phone' in visual_description or 'smartphone' in visual_description:
                        final_category = "Electronics"
                        final_name = "Smartphone"
                    elif 'watch' in visual_description:
                        final_category = "Electronics"
                        final_name = "Watch"
                    elif 'tablet' in visual_description:
                        final_category = "Electronics"
                        final_name = "Tablet"
                    elif 'shoes' in visual_description or 'footwear' in visual_description:
                        final_category = "Footwear"
                        final_name = "Shoes"
                    elif 'book' in visual_description:
                        final_category = "Books"
                        final_name = "Book"
                    elif 'clothing' in visual_description or 'apparel' in visual_description:
                        final_category = "Clothing"
                        final_name = "Clothing"
                    else:
                        final_name = "Product"
                    
                    # Add descriptive adjectives to the name
                    descriptors = []
                    if 'metallic' in visual_description:
                        descriptors.append("Metallic")
                    if 'monochrome' in visual_description:
                        descriptors.append("Monochrome")
                    if 'wide' in visual_description:
                        descriptors.append("Wide")
                    elif 'tall' in visual_description:
                        descriptors.append("Tall")
                    elif 'square' in visual_description:
                        descriptors.append("Square")
                    
                    if descriptors:
                        final_name = f"{' '.join(descriptors)} {final_name}"
                    
                    final_description = visual_description
                    final_confidence = visual_confidence
                
                else:
                    # Ultimate fallback
                    final_name = "Product"
                    final_description = "Visual analysis could not identify product type"
                    final_confidence = 0.1
            
            # Create ProductInfo object
            product_info = ProductInfo(
                name=final_name,
                brand=final_brand,
                category=final_category,
                description=final_description,
                extracted_text=extracted_text if meaningful_text else "",
                confidence=final_confidence
            )
            
            logger.info(f"Final product analysis: {final_name} (confidence: {final_confidence:.2f})")
            
            return product_info
            
        except Exception as e:
            logger.error(f"Error analyzing product image: {e}")
            return ProductInfo(
                name="Unknown Product",
                extracted_text="",
                confidence=0.0
            )

    def _has_meaningful_text(self, text: str) -> bool:
        """Check if extracted text is meaningful (not just OCR noise)"""
        if not text or len(text.strip()) < 2:
            return False
        
        # Check for common OCR noise patterns
        noise_patterns = [
            r'^[^a-zA-Z]*$',  # Only numbers/symbols
            r'^.{1,2}$',      # Too short (1-2 chars)
            r'^[IVXLCDM]+$',  # Only Roman numerals (common OCR error)
            r'^[0-9\s\-_.]+$' # Only numbers, spaces, and basic punctuation
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, text.strip()):
                return False
        
        # Check if text has at least one meaningful word
        words = text.split()
        meaningful_words = [word for word in words if len(word) >= 3 and word.isalpha()]
        
        return len(meaningful_words) > 0

# Global instance
vision_service = VisionService()