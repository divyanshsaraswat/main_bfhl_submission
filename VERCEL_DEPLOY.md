# Bill Extraction API - Vercel Deployment

## 🚀 Deploy to Vercel

This project is configured for Vercel serverless deployment.

### Quick Deploy

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy (first time)
vercel

# Deploy to production
vercel --prod
```

### Endpoints

After deployment, your API will be available at:

- **Extract**: `https://your-project.vercel.app/api/extract`
- **Health**: `https://your-project.vercel.app/api/health`

### Test Deployed API

```bash
curl -X POST "https://your-project.vercel.app/api/extract" \
  -H "Content-Type: application/json" \
  -d '{"document": "YOUR_DOCUMENT_URL"}'
```

### Configuration

The project includes:
- `api/extract.py` - Main extraction endpoint
- `api/health.py` - Health check endpoint
- `vercel.json` - Vercel configuration
- `requirements.txt` - Python dependencies

### Environment Variables (Optional)

Add in Vercel dashboard:
- `GOOGLE_APPLICATION_CREDENTIALS` - For Google Cloud Vision API
- `GEMINI_API_KEY` - For LLM-based page classification

---

**That's it! Your API is now serverless and scalable on Vercel! 🎉**
