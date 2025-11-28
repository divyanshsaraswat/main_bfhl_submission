# HackRx Bill Extraction - Quick Setup Guide

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Dependencies

```bash
# Activate virtual environment (if not already active)
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Keys (Optional)

For best results, set up Google Cloud Vision API:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Cloud Vision API"
4. Create service account and download JSON key
5. Save the JSON file securely
6. Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env`:
```
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
```

**Note**: The system will work without API keys using fallback OCR, but accuracy will be lower.

### Step 3: Start the Server

```bash
python run.py
```

Server will start at: http://localhost:8000

### Step 4: Test the API

Open another terminal and run:

```bash
python test_hackrx_api.py
```

Or test manually:

```bash
curl -X POST "http://localhost:8000/extract-bill-data" \
  -H "Content-Type: application/json" \
  -d '{"document": "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_2.png?sv=2025-07-05&spr=https&st=2025-11-24T14%3A13%3A22Z&se=2026-11-25T14%3A13%3A00Z&sr=b&sp=r&sig=WFJYfNw0PJdZOpOYlsoAW0XujYGG1x2HSbcDREiFXSU%3D"}'
```

### Step 5: View API Documentation

Open browser: http://localhost:8000/docs

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info |
| `/health` | GET | Health check |
| `/extract-bill-data` | POST | **HackRx endpoint** - Extract from document URL |
| `/extract` | POST | Legacy endpoint - Extract from OCR tokens |
| `/docs` | GET | Interactive API documentation |

## 🧪 Testing with Training Data

Download the training samples:

```bash
# Download from: https://hackrx.blob.core.windows.net/files/TRAINING_SAMPLES.zip?...
# Extract to test_data/ folder
```

Test each document:

```python
import requests

url = "http://localhost:8000/extract-bill-data"
payload = {"document": "YOUR_DOCUMENT_URL"}

response = requests.post(url, json=payload)
print(response.json())
```

## 🐛 Troubleshooting

**Server won't start:**
- Check if port 8000 is available
- Verify all dependencies installed: `pip list`

**OCR not working:**
- Check Google Cloud credentials path
- Verify Vision API is enabled in GCP
- Try without credentials (will use fallback)

**Low accuracy:**
- Use Google Cloud Vision API (not fallback)
- Ensure high-quality input images
- Check page classification results

**Import errors:**
- Make sure you're in the virtual environment
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

## 📚 Next Steps

1. **Read full documentation**: [README.md](README.md)
2. **Deploy to cloud**: [DEPLOYMENT.md](DEPLOYMENT.md)
3. **Review project structure**: [STRUCTURE.md](STRUCTURE.md)
4. **Test with your data**: Use the `/extract-bill-data` endpoint

## 🎯 For Hackathon Submission

1. ✅ API endpoint: `/extract-bill-data`
2. ✅ Request format: `{"document": "URL"}`
3. ✅ Response format: Matches HackRx specification exactly
4. ✅ Page classification: Bill Detail, Final Bill, Pharmacy
5. ✅ Token usage tracking: Included in response
6. ✅ Accuracy optimization: No missed items, no double-counting

## 📞 Support

Check the following files for help:
- **README.md**: Complete documentation
- **DEPLOYMENT.md**: Deployment instructions
- **STRUCTURE.md**: Project organization
- **test_hackrx_api.py**: Example usage

---

**Ready to deploy? See [DEPLOYMENT.md](DEPLOYMENT.md) for cloud deployment options!**
