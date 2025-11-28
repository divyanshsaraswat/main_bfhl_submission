"""
Vercel Serverless Function for Bill Extraction API
Main endpoint: /api/extract
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.models import OCRInput
from src.core.bill_extractor import BillExtractor
from src.api.hackrx_models import DocumentInput, HackRxResponse
from src.core.ocr_processor import OCRProcessor
from src.core.page_classifier import PageClassifier
from src.core.hackrx_adapter import HackRxAdapter


# Initialize components (reused across requests)
ocr_processor = OCRProcessor(use_google_vision=True)
page_classifier = PageClassifier(use_llm=False)


def handler(request):
    """
    Vercel serverless function handler for /api/extract
    
    Accepts: {"document": "https://example.com/bill.png"}
    Returns: HackRx formatted response
    """
    try:
        # Parse request
        if request.get("method") == "GET":
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "service": "Bill Extraction API",
                    "version": "2.0.0",
                    "endpoint": "/api/extract",
                    "method": "POST",
                    "docs": "https://github.com/divyanshsaraswat/main_bfhl_submission"
                }
            }
        
        # Get request body
        body = request.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)
        
        # Validate input
        if "document" not in body:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "is_success": False,
                    "message": "Missing 'document' field in request body"
                }
            }
        
        document_url = body["document"]
        
        # Step 1: Download and OCR
        try:
            tokens, total_pages = ocr_processor.process_document(document_url)
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "is_success": False,
                    "token_usage": {"total_tokens": 0, "input_tokens": 0, "output_tokens": 0},
                    "data": {"pagewise_line_items": [], "total_item_count": 0}
                }
            }
        
        if not tokens:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "is_success": False,
                    "token_usage": {"total_tokens": 0, "input_tokens": 0, "output_tokens": 0},
                    "data": {"pagewise_line_items": [], "total_item_count": 0}
                }
            }
        
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
        
        # Return response
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": response.model_dump()
        }
    
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": {
                "is_success": False,
                "message": f"Internal server error: {str(e)}"
            }
        }
