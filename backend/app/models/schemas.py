from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class ProductInfo(BaseModel):
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    extracted_text: Optional[str] = None
    confidence: float = 0.0

class PriceInfo(BaseModel):
    price: float
    currency: str = "USD"
    source: str
    url: str
    availability: str = "in_stock"
    shipping_info: Optional[str] = None
    last_updated: datetime

class ProductOffer(BaseModel):
    product_info: ProductInfo
    price_info: PriceInfo
    similarity_score: float = 1.0
    image_url: Optional[str] = None

class SearchResponse(BaseModel):
    exact_matches: List[ProductOffer]
    similar_products: List[ProductOffer]
    processing_time: float
    query_id: str

class UploadResponse(BaseModel):
    message: str
    filename: str
    product_info: ProductInfo
    query_id: str
    file_url: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[int] = None