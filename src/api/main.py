"""
FastAPI Application for Bill Extraction & Validation Agent
Provides REST API endpoints for bill processing
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
    title="Bill Extraction & Validation Agent",
    description="Production-grade API for extracting structured data from medical bills with fraud detection",
    version="1.0.0"
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
        "service": "Bill Extraction & Validation Agent",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "hackrx": "/extract-bill-data",
            "legacy": "/extract",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "bill-extraction-agent"
    }


@app.post("/extract-bill-data", response_model=HackRxResponse)
async def extract_bill_data(request: DocumentInput) -> HackRxResponse:
    """
    HackRx Bill Extraction Endpoint
    
    Accepts a document URL and returns structured bill data in HackRx format.
    
    **Input**: DocumentInput with document URL
    **Output**: HackRxResponse with pagewise line items and token usage
    """
    try:
        logger.info(f"Received HackRx extraction request for document: {request.document[:100]}...")
        
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
        
        # Step 3: Extract bill data using existing extractor
        extractor = BillExtractor()
        extraction_result = extractor.extract(ocr_input)
        
        logger.info(f"Extraction completed with status: {extraction_result.meta.status}")
        
        # Step 4: Convert to HackRx format
        adapter = HackRxAdapter(page_classifier)
        hackrx_response = adapter.convert_to_hackrx_format(extraction_result, tokens)
        
        logger.info(f"HackRx response prepared: {hackrx_response.data.total_item_count} items")
        
        return hackrx_response
    
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


@app.post("/extract", response_model=BillExtractionOutput)
async def extract_bill(ocr_input: OCRInput) -> BillExtractionOutput:
    """
    Main extraction endpoint (Legacy)
    
    Accepts OCR tokens and returns structured bill data with fraud detection.
    
    **Input**: OCRInput schema with tokens array
    **Output**: BillExtractionOutput with line items, totals, and fraud signals
    """
    try:
        logger.info(f"Received extraction request with {len(ocr_input.tokens)} tokens")
        
        # Create extractor and process
        extractor = BillExtractor()
        result = extractor.extract(ocr_input)
        
        logger.info(f"Extraction completed with status: {result.meta.status}")
        
        return result
    
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/extract-json")
async def extract_bill_from_json(data: Dict[str, Any]) -> JSONResponse:
    """
    Alternative endpoint accepting raw JSON
    
    Useful for testing and debugging
    """
    try:
        # Parse into OCRInput
        ocr_input = OCRInput(**data)
        
        # Extract
        extractor = BillExtractor()
        result = extractor.extract(ocr_input)
        
        # Return as JSON
        return JSONResponse(content=result.model_dump())
    
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/validate-input")
async def validate_input(ocr_input: OCRInput):
    """
    Validate OCR input without processing
    
    Useful for testing input format
    """
    return {
        "status": "valid",
        "token_count": len(ocr_input.tokens),
        "pages": ocr_input.total_pages
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

