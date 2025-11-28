"""
Vercel Serverless Function for Bill Extraction API
Main endpoint: /api/extract
"""

from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from pathlib import Path
from urllib.parse import parse_qs

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.models import OCRInput
from src.core.bill_extractor import BillExtractor
from src.api.hackrx_models import DocumentInput, HackRxResponse
from src.core.ocr_processor import OCRProcessor
from src.core.page_classifier import PageClassifier
from src.core.hackrx_adapter import HackRxAdapter


# Check for environment variables
GOOGLE_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Initialize components (reused across requests)
ocr_processor = OCRProcessor(use_google_vision=bool(GOOGLE_CREDENTIALS))
page_classifier = PageClassifier(use_llm=bool(GEMINI_API_KEY), llm_api_key=GEMINI_API_KEY)


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""
    
    def do_GET(self):
        """Handle GET requests"""
        # Build warning message if env vars not set
        warnings = []
        if not GOOGLE_CREDENTIALS:
            warnings.append("GOOGLE_APPLICATION_CREDENTIALS not set - using fallback OCR (lower accuracy)")
        if not GEMINI_API_KEY:
            warnings.append("GEMINI_API_KEY not set - using rule-based page classification")
        
        response_data = {
            "service": "Bill Extraction API",
            "version": "2.0.0",
            "endpoint": "/api/extract",
            "method": "POST",
            "docs": "https://github.com/divyanshsaraswat/main_bfhl_submission"
        }
        
        if warnings:
            response_data["warnings"] = warnings
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            # Parse JSON
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self._send_error(400, "Invalid JSON in request body")
                return
            
            # Validate input
            if "document" not in data:
                self._send_error(400, "Missing 'document' field in request body")
                return
            
            document_url = data["document"]
            
            # Step 1: Download and OCR
            try:
                tokens, total_pages = ocr_processor.process_document(document_url)
            except Exception as e:
                self._send_error(500, f"OCR processing failed: {str(e)}")
                return
            
            if not tokens:
                self._send_error(400, "No text extracted from document")
                return
            
            # Step 2: Create OCR input
            ocr_input = OCRInput(
                tokens=tokens,
                total_pages=total_pages,
                metadata={"source": document_url}
            )
            
            # Step 3: Extract bill data
            extractor = BillExtractor()
            extraction_result = extractor.extract(ocr_input)
            
            # Step 4: Convert to response format
            adapter = HackRxAdapter(page_classifier)
            response = adapter.convert_to_hackrx_format(extraction_result, tokens)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response.model_dump()).encode())
        
        except Exception as e:
            self._send_error(500, f"Internal server error: {str(e)}")
    
    def _send_error(self, status_code, message):
        """Send error response"""
        error_response = {
            "is_success": False,
            "message": message,
            "token_usage": {"total_tokens": 0, "input_tokens": 0, "output_tokens": 0},
            "data": {"pagewise_line_items": [], "total_item_count": 0}
        }
        
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(error_response).encode())
