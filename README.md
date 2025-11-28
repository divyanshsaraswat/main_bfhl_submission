# Bill Extraction API

Extract structured line item data from medical bills with high accuracy.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python run.py
```

Server runs at: **http://localhost:8000**

## 📋 API

### POST `/extract`

Extract bill data from a document URL.

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

### Other Endpoints

- `GET /` - Service info
- `GET /health` - Health check
- `GET /docs` - Interactive API docs

## 🧪 Testing

```bash
# Test the API
python test_hackrx_api.py

# Or use curl
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: application/json" \
  -d '{"document": "YOUR_DOCUMENT_URL"}'
```

## ⚙️ Configuration

### Optional: Google Cloud Vision (Recommended)

For best OCR accuracy:

1. Get service account JSON from [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Cloud Vision API
3. Set environment variable:
   ```bash
   set GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json
   ```

Without it, the API uses fallback OCR (lower accuracy).

## 📁 Project Structure

```
BFHL/
├── src/
│   ├── api/              # FastAPI application
│   │   ├── main.py       # API endpoints
│   │   └── hackrx_models.py
│   └── core/             # Extraction logic
│       ├── ocr_processor.py
│       ├── bill_extractor.py
│       ├── page_classifier.py
│       └── ...
├── config/               # Configuration
├── tests/                # Tests
├── run.py                # Server launcher
└── requirements.txt      # Dependencies
```

## 🎯 Features

- **Document URL Processing** - Direct image URL input
- **OCR Integration** - Google Cloud Vision with fallback
- **Page Classification** - Auto-categorizes pages (Bill Detail/Final Bill/Pharmacy)
- **Accurate Extraction** - Table parsing with column detection
- **No Missed Items** - Comprehensive extraction strategies
- **No Double-Counting** - Deduplication logic

## 🚢 Deployment

### Vercel (Recommended - Serverless)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

Your API will be at: `https://your-project.vercel.app/api/extract`

### Render (Free)

1. Create account at [render.com](https://render.com)
2. Connect GitHub repository
3. Create Web Service
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables (optional):
   - `GOOGLE_APPLICATION_CREDENTIALS` (as secret file)
7. Deploy

### Railway

1. Create account at [railway.app](https://railway.app)
2. Deploy from GitHub
3. Railway auto-detects Python
4. Add environment variables
5. Deploy

## 🔧 Troubleshooting

**Server won't start?**
- Check port 8000 is available
- Verify virtual environment is active

**Low accuracy?**
- Set up Google Cloud Vision API
- Ensure high-quality input images

**Import errors?**
- Reinstall: `pip install -r requirements.txt --force-reinstall`

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs (when server running)
- **GitHub**: [Repository Link](https://github.com/divyanshsaraswat/main_bfhl_submission)

---

**Version**: 2.0.0  
**License**: MIT
