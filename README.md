# HackRx Bill Extraction API

A production-grade bill extraction system that processes medical bills from document images and extracts structured line item data with high accuracy.

## 🎯 Problem Statement

Extract line item details from multi-page medical bills including:
- Individual line item amounts, rates, and quantities
- Sub-totals (where they exist)
- Final total with accurate reconciliation
- Ensure no missed items and no double-counting

## ✨ Features

- **Document URL Processing**: Accepts image URLs directly
- **OCR Integration**: Google Cloud Vision API with fallback support
- **Smart Page Classification**: Categorizes pages as "Bill Detail", "Final Bill", or "Pharmacy"
- **Accurate Extraction**: Table parsing with column detection
- **Fraud Detection**: Identifies arithmetic mismatches and anomalies
- **Token Tracking**: Monitors LLM API usage
- **REST API**: FastAPI-based with automatic documentation

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Cloud Vision API credentials (optional but recommended)

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd BFHL

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables (optional)
cp .env.example .env
# Edit .env and add your Google Cloud credentials
```

### Running the Server

```bash
# Start the server
python run.py

# Server will be available at:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - Health: http://localhost:8000/health
```

### Testing the API

```bash
# Test with the provided test script
python test_hackrx_api.py

# Or use curl
curl -X POST "http://localhost:8000/extract-bill-data" \
  -H "Content-Type: application/json" \
  -d '{"document": "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_2.png?..."}'
```

## 📋 API Specification

### Endpoint: `/extract-bill-data`

**Request:**
```json
{
  "document": "https://example.com/bill.png"
}
```

**Response:**
```json
{
  "is_success": true,
  "token_usage": {
    "total_tokens": 0,
    "input_tokens": 0,
    "output_tokens": 0
  },
  "data": {
    "pagewise_line_items": [
      {
        "page_no": "1",
        "page_type": "Bill Detail",
        "bill_items": [
          {
            "item_name": "Consultation Fee",
            "item_amount": 500.0,
            "item_rate": 500.0,
            "item_quantity": 1.0
          }
        ]
      }
    ],
    "total_item_count": 1
  }
}
```

## 🏗️ Architecture

```
BFHL/
├── src/
│   ├── core/                    # Core extraction logic
│   │   ├── ocr_processor.py     # Document download & OCR
│   │   ├── page_classifier.py   # Page type classification
│   │   ├── bill_extractor.py    # Main extraction engine
│   │   ├── table_parser.py      # Table structure parsing
│   │   ├── hackrx_adapter.py    # Format conversion
│   │   ├── fraud_detector.py    # Fraud detection
│   │   ├── models.py            # Internal data models
│   │   └── utils.py             # Utility functions
│   └── api/                     # API layer
│       ├── main.py              # FastAPI application
│       └── hackrx_models.py     # HackRx API schemas
├── config/                      # Configuration
├── tests/                       # Test suite
├── test_data/                   # Sample data
├── run.py                       # Server launcher
├── test_hackrx_api.py          # API test script
└── requirements.txt             # Dependencies
```

## 🔧 Configuration

### OCR Service

The system supports multiple OCR backends:

1. **Google Cloud Vision** (Recommended)
   - Set `GOOGLE_APPLICATION_CREDENTIALS` in `.env`
   - Best accuracy for medical bills

2. **Tesseract OCR** (Fallback)
   - Install: `pip install pytesseract`
   - Free but lower accuracy

### Page Classification

Two modes available:

1. **Rule-based** (Default)
   - No API key required
   - Uses keyword matching

2. **LLM-based** (Optional)
   - Set `GEMINI_API_KEY` in `.env`
   - Higher accuracy

## 📊 Accuracy Optimization

The system ensures high accuracy through:

1. **No Missed Items**: Comprehensive table parsing with multiple fallback strategies
2. **No Double-Counting**: Deduplication based on page, row, and content
3. **Reconciliation**: Compares extracted total vs. actual bill total
4. **Confidence Scoring**: Each item has a confidence score
5. **Fraud Detection**: Identifies arithmetic errors and anomalies

## 🧪 Testing

```bash
# Run unit tests
python -m pytest tests/

# Run integration test
python test_hackrx_api.py

# Test specific document
curl -X POST "http://localhost:8000/extract-bill-data" \
  -H "Content-Type: application/json" \
  -d '{"document": "YOUR_DOCUMENT_URL"}'
```

## 🚢 Deployment

### Option 1: Render

1. Create account at [render.com](https://render.com)
2. Connect your GitHub repository
3. Create new Web Service
4. Set environment variables
5. Deploy

### Option 2: Railway

1. Create account at [railway.app](https://railway.app)
2. Connect GitHub repository
3. Add environment variables
4. Deploy

### Option 3: Docker

```bash
# Build image
docker build -t bill-extractor .

# Run container
docker run -p 8000:8000 -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json bill-extractor
```

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google Cloud service account JSON | Recommended |
| `GEMINI_API_KEY` | Google Gemini API key for LLM classification | Optional |
| `HOST` | Server host (default: 0.0.0.0) | No |
| `PORT` | Server port (default: 8000) | No |

## 🔍 Troubleshooting

**OCR not working?**
- Check Google Cloud credentials
- Verify API is enabled in GCP console
- Try fallback: `pip install pytesseract`

**Low accuracy?**
- Ensure high-quality input images
- Check page classification results
- Review confidence scores in output

**Server not starting?**
- Check port 8000 is available
- Verify all dependencies installed
- Check logs for errors

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs (when server running)
- **Implementation Plan**: [docs/implementation_plan.md](docs/implementation_plan.md)
- **Project Overview**: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)

## 🤝 Contributing

This is a hackathon submission. For questions or issues, please contact the development team.

## 📄 License

MIT License - See LICENSE file for details

---

**Version**: 2.0.0 (HackRx Edition)  
**Last Updated**: 2025-11-28
