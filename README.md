# Vision Price Hunt

A full-stack web application that uses computer vision to identify products from images and finds the best available prices across multiple e-commerce platforms.

## Features

🔍 **AI-Powered Product Recognition**
- Upload any product image
- OCR text extraction from product images
- Computer vision-based product identification
- Automatic brand and category detection

🛒 **Multi-Source Price Comparison**
- Searches across multiple e-commerce platforms
- Real-time price comparison
- Availability status tracking
- Source reliability scoring

📊 **Smart Ranking & Recommendations**
- Price-based ranking with multiple factors
- Similarity scoring for product matching
- Exact matches vs similar product suggestions
- Trust scores for different sources

🎨 **Modern UI/UX**
- Responsive, mobile-first design
- Drag-and-drop image upload
- Clean card-based interface
- Real-time loading states and feedback

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Computer Vision** - PIL, OpenCV for image processing
- **OCR** - pytesseract for text extraction
- **ML/AI** - sentence-transformers for semantic similarity
- **Web Scraping** - requests, BeautifulSoup for price data
- **Data Processing** - Pydantic for data validation

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type safety and better developer experience
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Modern UI component library
- **Lucide React** - Beautiful icons

## Architecture

```
vision-price-hunt/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/endpoints/   # API route handlers
│   │   ├── services/        # Business logic services
│   │   ├── models/          # Data models and schemas
│   │   └── core/            # Configuration and utilities
│   └── requirements.txt     # Python dependencies
├── frontend/                # Next.js frontend
│   ├── src/
│   │   ├── app/            # Next.js app router pages
│   │   ├── components/     # React components
│   │   └── lib/            # Utilities and helpers
│   └── package.json        # Node.js dependencies
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.8+ for backend
- Node.js 18+ for frontend
- pip and npm package managers

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install additional system dependencies for OCR:
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

5. Start the backend server:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## API Documentation

### Endpoints

#### POST /api/upload
Upload and analyze a product image.

**Request:**
- `file`: Image file (JPG, PNG, WEBP, max 10MB)

**Response:**
```json
{
  "message": "Image uploaded and analyzed successfully",
  "filename": "product.jpg",
  "product_info": {
    "name": "iPhone 15 Pro Max",
    "brand": "Apple",
    "category": "Electronics",
    "description": "iPhone 15 Pro Max 256GB Space Black",
    "extracted_text": "iPhone 15 Pro Max 256GB Space Black Apple",
    "confidence": 0.95
  },
  "query_id": "uuid-string",
  "file_url": "/uploads/filename.jpg"
}
```

#### POST /api/search
Search for products and prices based on product information.

**Request:**
```json
{
  "name": "iPhone 15 Pro Max",
  "brand": "Apple",
  "category": "Electronics",
  "description": "iPhone 15 Pro Max 256GB Space Black"
}
```

**Response:**
```json
{
  "exact_matches": [
    {
      "product_info": {
        "name": "iPhone 15 Pro Max 256GB",
        "brand": "Apple",
        "category": "Electronics"
      },
      "price_info": {
        "price": 1199.99,
        "currency": "USD",
        "source": "Apple Store",
        "url": "https://apple.com/product",
        "availability": "in_stock",
        "last_updated": "2024-01-01T00:00:00Z"
      },
      "similarity_score": 0.95
    }
  ],
  "similar_products": [...],
  "processing_time": 2.34,
  "query_id": "uuid-string"
}
```

#### GET /health
Health check endpoint for both upload and search services.

### Interactive API Documentation

When the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Configuration

### Backend Configuration

Edit `backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    # Upload settings
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: List[str] = [".jpg", ".jpeg", ".png", ".webp"]
    
    # Vision service settings
    ocr_confidence_threshold: float = 0.5
    similarity_threshold: float = 0.7
    max_similar_products: int = 10
    
    # Scraper settings
    request_timeout: int = 30
    max_retries: int = 3
```

### Frontend Configuration

Edit `frontend/next.config.ts` for Next.js settings.

## Development

### Adding New Price Sources

1. Create a new method in `backend/app/services/scraper.py`:
```python
async def search_new_source(self, query: str) -> List[ProductOffer]:
    # Implementation for new source
    pass
```

2. Add the new source to `scrape_all_sources()`:
```python
tasks = [
    self.search_amazon(query),
    self.search_ebay(query),
    self.search_new_source(query),  # Add here
]
```

### Improving Vision Recognition

1. Enhance OCR preprocessing in `backend/app/services/vision.py`
2. Add new brand/category patterns
3. Implement additional ML models for better accuracy

### UI Customization

1. Modify components in `frontend/src/components/`
2. Update Tailwind classes for styling
3. Add new UI components following shadcn/ui patterns

## Deployment

### Docker Deployment

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

### Production Considerations

1. **Security**: Add authentication, rate limiting, input validation
2. **Performance**: Implement caching, CDN, image optimization
3. **Monitoring**: Add logging, error tracking, performance monitoring
4. **Scaling**: Use load balancers, database clustering, microservices

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Commit your changes: `git commit -am 'Add feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python web framework
- [Next.js](https://nextjs.org/) for the React framework
- [shadcn/ui](https://ui.shadcn.com/) for the beautiful UI components
- [Tailwind CSS](https://tailwindcss.com/) for the utility-first CSS framework
- Various open-source libraries that made this project possible

## Support

For support, email support@visionpricehunt.com or create an issue in the GitHub repository.