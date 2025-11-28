"""
OCR Processor Module
Handles document download and OCR processing using Google Cloud Vision API
"""

import io
import os
import requests
from typing import List, Tuple, Optional
from pathlib import Path
from PIL import Image
import logging

from src.core.models import OCRToken

logger = logging.getLogger(__name__)


class OCRProcessor:
    """Processes documents from URLs and extracts OCR tokens"""
    
    def __init__(self, use_google_vision: bool = True):
        """
        Initialize OCR processor
        
        Args:
            use_google_vision: If True, use Google Cloud Vision API, else use fallback
        """
        self.use_google_vision = use_google_vision
        self.vision_client = None
        
        if use_google_vision:
            try:
                from google.cloud import vision
                self.vision_client = vision.ImageAnnotatorClient()
                logger.info("Google Cloud Vision API initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Vision API: {e}")
                logger.info("Falling back to basic OCR")
                self.use_google_vision = False
    
    def download_document(self, url: str, timeout: int = 30) -> bytes:
        """
        Download document from URL
        
        Args:
            url: Document URL
            timeout: Request timeout in seconds
            
        Returns:
            Document content as bytes
        """
        try:
            logger.info(f"Downloading document from: {url[:100]}...")
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            logger.info(f"Downloaded {len(response.content)} bytes, type: {content_type}")
            
            return response.content
        except Exception as e:
            logger.error(f"Failed to download document: {e}")
            raise ValueError(f"Failed to download document: {str(e)}")
    
    def process_document(self, url: str) -> Tuple[List[OCRToken], int]:
        """
        Download and process document to extract OCR tokens
        
        Args:
            url: Document URL
            
        Returns:
            Tuple of (OCR tokens list, total pages)
        """
        # Download document
        content = self.download_document(url)
        
        # Detect if multi-page (PDF) or single image
        total_pages = self._detect_pages(content)
        
        # Process based on type
        if self.use_google_vision and self.vision_client:
            tokens = self._process_with_google_vision(content, total_pages)
        else:
            tokens = self._process_with_fallback(content, total_pages)
        
        logger.info(f"Extracted {len(tokens)} tokens from {total_pages} page(s)")
        return tokens, total_pages
    
    def _detect_pages(self, content: bytes) -> int:
        """Detect number of pages in document"""
        try:
            # Try to open as image
            image = Image.open(io.BytesIO(content))
            # Check if multi-page (e.g., TIFF)
            try:
                page_count = 0
                while True:
                    image.seek(page_count)
                    page_count += 1
            except EOFError:
                return page_count if page_count > 0 else 1
        except Exception as e:
            logger.warning(f"Could not detect pages: {e}, assuming 1 page")
            return 1
    
    def _process_with_google_vision(self, content: bytes, total_pages: int) -> List[OCRToken]:
        """Process document using Google Cloud Vision API"""
        from google.cloud import vision
        
        tokens = []
        
        try:
            image = vision.Image(content=content)
            response = self.vision_client.document_text_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Google Vision API error: {response.error.message}")
            
            # Extract tokens from response
            for page_idx, page in enumerate(response.full_text_annotation.pages, start=1):
                for block in page.blocks:
                    for paragraph in block.paragraphs:
                        for word in paragraph.words:
                            # Get word text
                            word_text = ''.join([symbol.text for symbol in word.symbols])
                            
                            # Get bounding box
                            vertices = word.bounding_box.vertices
                            bbox = [
                                vertices[0].x,  # x1
                                vertices[0].y,  # y1
                                vertices[2].x,  # x2
                                vertices[2].y   # y2
                            ]
                            
                            # Get confidence
                            confidence = word.confidence if hasattr(word, 'confidence') else 0.9
                            
                            tokens.append(OCRToken(
                                text=word_text,
                                bbox=bbox,
                                page=page_idx,
                                confidence=confidence
                            ))
            
            logger.info(f"Google Vision extracted {len(tokens)} tokens")
            
        except Exception as e:
            logger.error(f"Google Vision processing failed: {e}")
            logger.info("Falling back to basic OCR")
            tokens = self._process_with_fallback(content, total_pages)
        
        return tokens
    
    def _process_with_fallback(self, content: bytes, total_pages: int) -> List[OCRToken]:
        """
        Fallback OCR processing using pytesseract or basic image analysis
        This is a simplified version for when Google Vision is not available
        """
        try:
            import pytesseract
            from PIL import Image
            
            tokens = []
            image = Image.open(io.BytesIO(content))
            
            # Get OCR data with bounding boxes
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i].strip()
                if not text:
                    continue
                
                x, y, w, h = (
                    ocr_data['left'][i],
                    ocr_data['top'][i],
                    ocr_data['width'][i],
                    ocr_data['height'][i]
                )
                
                confidence = float(ocr_data['conf'][i]) / 100.0 if ocr_data['conf'][i] != -1 else 0.5
                
                tokens.append(OCRToken(
                    text=text,
                    bbox=[x, y, x + w, y + h],
                    page=1,  # Tesseract processes single page at a time
                    confidence=max(0.0, min(1.0, confidence))
                ))
            
            logger.info(f"Fallback OCR extracted {len(tokens)} tokens")
            return tokens
            
        except ImportError:
            logger.error("pytesseract not available, using mock tokens")
            return self._create_mock_tokens()
    
    def _create_mock_tokens(self) -> List[OCRToken]:
        """Create mock tokens for testing when no OCR is available"""
        logger.warning("Creating mock OCR tokens - install Google Cloud Vision or pytesseract for real OCR")
        
        # Return empty list - actual processing will fail gracefully
        return []
