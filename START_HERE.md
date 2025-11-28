# 🚀 Quick Start - Server is Ready!

## ✅ All Import Issues Fixed!

The server is now ready to run. All import errors have been resolved.

## Start the Server

Open a terminal and run:

```bash
python run.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Test the API

### Option 1: Use the Test Script

Open a **NEW terminal** (keep the server running) and run:

```bash
python test_hackrx_api.py
```

### Option 2: Test with curl

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "bill-extraction-agent"
}
```

### Option 3: Open API Documentation

Open your browser and go to:
```
http://localhost:8000/docs
```

You'll see interactive API documentation where you can test the `/extract-bill-data` endpoint directly!

## Test with a Sample Document

```bash
curl -X POST "http://localhost:8000/extract-bill-data" \
  -H "Content-Type: application/json" \
  -d "{\"document\": \"https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_2.png?sv=2025-07-05&spr=https&st=2025-11-24T14%3A13%3A22Z&se=2026-11-25T14%3A13%3A00Z&sr=b&sp=r&sig=WFJYfNw0PJdZOpOYlsoAW0XujYGG1x2HSbcDREiFXSU%3D\"}"
```

## ⚠️ Important Notes

### Google Cloud Vision API (Optional)

The server will work WITHOUT Google Cloud Vision API, but accuracy will be lower. You'll see this warning:
```
WARNING - Failed to initialize Google Vision API: No module named 'google.cloud'
INFO - Falling back to basic OCR
```

To enable Google Cloud Vision for better accuracy:

1. Install the package (already in requirements.txt):
   ```bash
   pip install google-cloud-vision
   ```

2. Set up credentials:
   - Get a service account JSON key from Google Cloud Console
   - Set environment variable:
     ```bash
     set GOOGLE_APPLICATION_CREDENTIALS=path\to\your\key.json
     ```

3. Restart the server

### Expected Behavior

- **Without Google Cloud Vision**: Server works with fallback OCR (pytesseract or mock)
- **With Google Cloud Vision**: Much better OCR accuracy for production use

## Troubleshooting

**Server won't start?**
- Make sure port 8000 is not in use
- Check that you're in the virtual environment: `venv\Scripts\activate`

**Test script fails?**
- Make sure the server is running first
- Check the server terminal for errors

**Low accuracy?**
- Set up Google Cloud Vision API (see above)
- Ensure input images are high quality

## Next Steps

1. ✅ Start server: `python run.py`
2. ✅ Test health: `curl http://localhost:8000/health`
3. ✅ Run tests: `python test_hackrx_api.py`
4. 📚 Read full docs: `README.md`
5. 🚀 Deploy: See `DEPLOYMENT.md`

---

**Everything is ready! Start the server and begin testing! 🎉**
