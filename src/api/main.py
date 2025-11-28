"""
FastAPI Application for HackRx Bill Extraction
Provides REST API endpoint for bill processing from document URLs
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
import logging
from typing import Dict, Any
import sys
from pathlib import Path
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.models import OCRInput, BillExtractionOutput
from src.core.bill_extractor import BillExtractor
from src.api.hackrx_models import DocumentInput, HackRxResponse, ErrorResponse
from src.core.ocr_processor import OCRProcessor
from src.core.page_classifier import PageClassifier
from src.core.hackrx_adapter import HackRxAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Bill Extraction API",
    description="Extract structured data from medical bills",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
ocr_processor = OCRProcessor(use_google_vision=True)
page_classifier = PageClassifier(
    use_llm=False,  # Set to True if you have Gemini API key
    llm_api_key=os.getenv('GEMINI_API_KEY')
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Bill Extraction API",
        "version": "2.0.0",
        "status": "running",
        "endpoint": "/extract",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "bill-extraction"
    }


@app.post("/extract", response_model=HackRxResponse)
async def extract_bill_data(request: DocumentInput) -> HackRxResponse:
    """
    Bill Extraction Endpoint
    
    Accepts a document URL and returns structured bill data.
    
    **Input**: Document URL
    **Output**: Pagewise line items with amounts, rates, and quantities
    
    **Example Request:**
    ```json
    {
      "document": "https://example.com/bill.png"
    }
    ```
    
    **Example Response:**
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
    """
    try:
        logger.info(f"Received extraction request for document: {request.document[:100]}...")
        
        # Step 1: Download and OCR the document
        try:
            tokens, total_pages = ocr_processor.process_document(request.document)
            logger.info(f"OCR completed: {len(tokens)} tokens from {total_pages} pages")
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            return HackRxResponse(
                is_success=False,
                token_usage={"total_tokens": 0, "input_tokens": 0, "output_tokens": 0},
                data={"pagewise_line_items": [], "total_item_count": 0}
            )
        
        if not tokens:
            logger.warning("No tokens extracted from document")
            return HackRxResponse(
                is_success=False,
                token_usage={"total_tokens": 0, "input_tokens": 0, "output_tokens": 0},
                data={"pagewise_line_items": [], "total_item_count": 0}
            )
        
        # Step 2: Create OCR input for bill extractor
        ocr_input = OCRInput(
            tokens=tokens,
            total_pages=total_pages,
            metadata={"source": request.document}
        )
        
        # Step 3: Extract bill data
        extractor = BillExtractor()
        extraction_result = extractor.extract(ocr_input)
        
        logger.info(f"Extraction completed with status: {extraction_result.meta.status}")
        
        # Step 4: Convert to response format
        adapter = HackRxAdapter(page_classifier)
        response = adapter.convert_to_hackrx_format(extraction_result, tokens)
        
        logger.info(f"Response prepared: {response.data.total_item_count} items")
        
        return response
    
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}", exc_info=True)
        return HackRxResponse(
            is_success=False,
            token_usage={"total_tokens": 0, "input_tokens": 0, "output_tokens": 0},
            data={"pagewise_line_items": [], "total_item_count": 0}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

