"""
Page Classifier Module
Classifies bill pages into types: Bill Detail, Final Bill, or Pharmacy
"""

import logging
from typing import List, Literal
from collections import Counter

from src.core.models import OCRToken

logger = logging.getLogger(__name__)

PageType = Literal["Bill Detail", "Final Bill", "Pharmacy"]


class PageClassifier:
    """Classifies pages based on content analysis"""
    
    # Keywords for page type detection
    FINAL_BILL_KEYWORDS = [
        'final', 'total', 'grand total', 'net payable', 'amount payable',
        'total amount', 'bill total', 'summary', 'payment'
    ]
    
    PHARMACY_KEYWORDS = [
        'pharmacy', 'medicine', 'medication', 'drug', 'tablet', 'capsule',
        'syrup', 'injection', 'prescription', 'rx', 'pharmaceutical'
    ]
    
    BILL_DETAIL_KEYWORDS = [
        'description', 'item', 'service', 'charge', 'procedure', 'test',
        'consultation', 'room', 'bed', 'treatment', 'diagnosis'
    ]
    
    def __init__(self, use_llm: bool = False, llm_api_key: str = None):
        """
        Initialize page classifier
        
        Args:
            use_llm: If True, use LLM for classification
            llm_api_key: API key for LLM service
        """
        self.use_llm = use_llm
        self.llm_api_key = llm_api_key
        
        if use_llm and llm_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=llm_api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                logger.info("LLM-based page classifier initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM: {e}, using rule-based classifier")
                self.use_llm = False
        else:
            logger.info("Using rule-based page classifier")
    
    def classify_page(self, tokens: List[OCRToken], page_num: int) -> PageType:
        """
        Classify a page based on its tokens
        
        Args:
            tokens: OCR tokens from the page
            page_num: Page number
            
        Returns:
            Page type classification
        """
        if self.use_llm:
            return self._classify_with_llm(tokens, page_num)
        else:
            return self._classify_with_rules(tokens, page_num)
    
    def _classify_with_rules(self, tokens: List[OCRToken], page_num: int) -> PageType:
        """Rule-based classification using keyword matching"""
        
        # Combine all text from page
        page_text = ' '.join([token.text.lower() for token in tokens])
        
        # Count keyword matches for each category
        final_bill_score = sum(1 for kw in self.FINAL_BILL_KEYWORDS if kw in page_text)
        pharmacy_score = sum(1 for kw in self.PHARMACY_KEYWORDS if kw in page_text)
        bill_detail_score = sum(1 for kw in self.BILL_DETAIL_KEYWORDS if kw in page_text)
        
        # Check for explicit "total" or "grand total" indicators
        has_total = any(word in page_text for word in ['grand total', 'final total', 'net payable'])
        
        # Check for table structure (multiple rows with amounts)
        amount_pattern_count = sum(1 for token in tokens if self._looks_like_amount(token.text))
        has_table_structure = amount_pattern_count >= 3
        
        # Decision logic
        if has_total and final_bill_score >= 2:
            return "Final Bill"
        elif pharmacy_score >= 2:
            return "Pharmacy"
        elif has_table_structure and bill_detail_score >= 2:
            return "Bill Detail"
        elif final_bill_score > pharmacy_score and final_bill_score > bill_detail_score:
            return "Final Bill"
        elif pharmacy_score > bill_detail_score:
            return "Pharmacy"
        else:
            # Default: if it has itemized structure, it's Bill Detail
            return "Bill Detail" if has_table_structure else "Final Bill"
    
    def _classify_with_llm(self, tokens: List[OCRToken], page_num: int) -> PageType:
        """LLM-based classification using Gemini"""
        try:
            # Prepare text sample (first 500 chars to save tokens)
            page_text = ' '.join([token.text for token in tokens[:100]])
            
            prompt = f"""Classify this bill page into one of these categories:
1. "Bill Detail" - Contains itemized list of charges/services
2. "Final Bill" - Contains summary and final total amount
3. "Pharmacy" - Contains medication/pharmaceutical items

Page text sample:
{page_text}

Respond with ONLY one of: Bill Detail, Final Bill, or Pharmacy"""
            
            response = self.model.generate_content(prompt)
            classification = response.text.strip()
            
            # Validate response
            if classification in ["Bill Detail", "Final Bill", "Pharmacy"]:
                logger.info(f"LLM classified page {page_num} as: {classification}")
                return classification
            else:
                logger.warning(f"Invalid LLM response: {classification}, falling back to rules")
                return self._classify_with_rules(tokens, page_num)
                
        except Exception as e:
            logger.error(f"LLM classification failed: {e}, using rules")
            return self._classify_with_rules(tokens, page_num)
    
    def _looks_like_amount(self, text: str) -> bool:
        """Check if text looks like a monetary amount"""
        # Remove common currency symbols and whitespace
        cleaned = text.replace('₹', '').replace('$', '').replace(',', '').strip()
        
        # Check if it's a number with optional decimal
        try:
            float(cleaned)
            return True
        except ValueError:
            return False
