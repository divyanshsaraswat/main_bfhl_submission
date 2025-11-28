# Deployment Guide - HackRx Bill Extraction API

This guide covers deploying your bill extraction API to various cloud platforms.

## Prerequisites

- GitHub repository with your code
- Google Cloud Vision API credentials (service account JSON)
- (Optional) Gemini API key for LLM-based classification

## Option 1: Render (Recommended)

Render offers free hosting with automatic deployments from GitHub.

### Steps:

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository

3. **Configure Service**
   ```
   Name: bill-extraction-api
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
   ```

4. **Add Environment Variables**
   - Click "Environment" tab
   - Add variables:
     ```
     GOOGLE_APPLICATION_CREDENTIALS=/etc/secrets/gcp-credentials.json
     GEMINI_API_KEY=your_key_here (optional)
     ```

5. **Add Secret Files**
   - Go to "Secret Files" tab
   - Add file: `/etc/secrets/gcp-credentials.json`
   - Paste your Google Cloud service account JSON

6. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Your API will be at: `https://your-service.onrender.com`

### Testing Deployed API:

```bash
curl -X POST "https://your-service.onrender.com/extract-bill-data" \
  -H "Content-Type: application/json" \
  -d '{"document": "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_2.png?..."}'
```

---

## Option 2: Railway

Railway provides simple deployment with generous free tier.

### Steps:

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure**
   - Railway auto-detects Python
   - Add start command in `railway.toml`:
     ```toml
     [build]
     builder = "NIXPACKS"

     [deploy]
     startCommand = "uvicorn src.api.main:app --host 0.0.0.0 --port $PORT"
     ```

4. **Add Environment Variables**
   - Go to "Variables" tab
   - Add:
     ```
     GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json
     GEMINI_API_KEY=your_key_here
     ```

5. **Add Service Account**
   - Create file `gcp-credentials.json` in repository root
   - Add to `.gitignore` (don't commit!)
   - Upload via Railway dashboard or use secrets

6. **Deploy**
   - Railway auto-deploys on push
   - Get URL from dashboard

---

## Option 3: Heroku

### Steps:

1. **Install Heroku CLI**
   ```bash
   # Download from heroku.com/cli
   ```

2. **Login**
   ```bash
   heroku login
   ```

3. **Create App**
   ```bash
   heroku create your-app-name
   ```

4. **Add Buildpack**
   ```bash
   heroku buildpacks:set heroku/python
   ```

5. **Create Procfile**
   ```
   web: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
   ```

6. **Set Environment Variables**
   ```bash
   # Upload GCP credentials as base64
   cat gcp-credentials.json | base64 > gcp-creds-base64.txt
   heroku config:set GCP_CREDENTIALS_BASE64=$(cat gcp-creds-base64.txt)
   heroku config:set GEMINI_API_KEY=your_key_here
   ```

7. **Update Code to Decode Credentials**
   Add to `src/api/main.py`:
   ```python
   import os
   import base64
   
   # Decode GCP credentials
   if os.getenv('GCP_CREDENTIALS_BASE64'):
       creds = base64.b64decode(os.getenv('GCP_CREDENTIALS_BASE64'))
       with open('/tmp/gcp-credentials.json', 'wb') as f:
           f.write(creds)
       os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/tmp/gcp-credentials.json'
   ```

8. **Deploy**
   ```bash
   git push heroku main
   ```

---

## Option 4: Docker + Any Platform

### Create Dockerfile:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and Run:

```bash
# Build
docker build -t bill-extractor .

# Run locally
docker run -p 8000:8000 \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json \
  -v $(pwd)/gcp-credentials.json:/app/gcp-credentials.json \
  bill-extractor

# Push to Docker Hub
docker tag bill-extractor your-username/bill-extractor
docker push your-username/bill-extractor
```

### Deploy to Cloud Run (Google Cloud):

```bash
# Build and push
gcloud builds submit --tag gcr.io/YOUR_PROJECT/bill-extractor

# Deploy
gcloud run deploy bill-extractor \
  --image gcr.io/YOUR_PROJECT/bill-extractor \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Testing Deployment

### Health Check:
```bash
curl https://your-deployed-url.com/health
```

### Extract Bill:
```bash
curl -X POST "https://your-deployed-url.com/extract-bill-data" \
  -H "Content-Type: application/json" \
  -d '{
    "document": "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_2.png?sv=2025-07-05&spr=https&st=2025-11-24T14%3A13%3A22Z&se=2026-11-25T14%3A13%3A00Z&sr=b&sp=r&sig=WFJYfNw0PJdZOpOYlsoAW0XujYGG1x2HSbcDREiFXSU%3D"
  }'
```

### Import Postman Collection:
1. Download the [HackRx Postman Collection](https://hackrx.blob.core.windows.net/assets/datathon-IIT/HackRx%20Bill%20Extraction%20API.postman_collection.json?...)
2. Import to Postman
3. Set `base_url` variable to your deployed URL
4. Test the endpoint

---

## Monitoring & Logs

### Render:
- View logs in dashboard under "Logs" tab
- Set up alerts for errors

### Railway:
- View logs in dashboard
- Use Railway CLI: `railway logs`

### Heroku:
```bash
heroku logs --tail
```

### Docker/Cloud Run:
```bash
# Cloud Run
gcloud logging read "resource.type=cloud_run_revision"

# Docker
docker logs <container-id>
```

---

## Performance Optimization

1. **Enable Caching**
   - Cache OCR results for repeated documents
   - Use Redis for session storage

2. **Async Processing**
   - For large documents, use background tasks
   - Return job ID, poll for results

3. **Rate Limiting**
   - Implement rate limiting to prevent abuse
   - Use slowapi or similar

4. **Monitoring**
   - Set up Sentry for error tracking
   - Use Prometheus for metrics

---

## Security Checklist

- [ ] Don't commit API keys or credentials
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS (automatic on most platforms)
- [ ] Implement rate limiting
- [ ] Validate input URLs
- [ ] Set CORS appropriately
- [ ] Monitor for unusual activity

---

## Troubleshooting

**Deployment fails:**
- Check build logs
- Verify requirements.txt is complete
- Ensure start command is correct

**OCR not working:**
- Verify GCP credentials are uploaded correctly
- Check API is enabled in Google Cloud Console
- Test credentials locally first

**Timeout errors:**
- Increase timeout in platform settings
- Optimize OCR processing
- Consider async processing for large files

**Out of memory:**
- Increase memory allocation in platform settings
- Optimize image processing
- Process pages sequentially instead of parallel

---

## Support

For deployment issues:
1. Check platform-specific documentation
2. Review application logs
3. Test locally first
4. Contact platform support if needed

---

**Good luck with your deployment! 🚀**
