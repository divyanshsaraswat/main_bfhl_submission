"""
HackRx Adapter Module
Bridges existing BillExtractor to HackRx API format
"""

import logging
from typing import List, Dict
from collections import defaultdict

from src.core.models import OCRToken, BillExtractionOutput, LineItem
from src.api.hackrx_models import (
    HackRxResponse, HackRxData, PagewiseLineItem, BillItem, TokenUsage
)
from src.core.page_classifier import PageClassifier

logger = logging.getLogger(__name__)


class HackRxAdapter:
    """Adapts internal extraction format to HackRx API format"""
    
    def __init__(self, page_classifier: PageClassifier):
        """
        Initialize adapter
        
        Args:
            page_classifier: Page classifier instance
        """
        self.page_classifier = page_classifier
        self.token_usage = TokenUsage()
    
    def convert_to_hackrx_format(
        self,
        extraction_output: BillExtractionOutput,
        all_tokens: List[OCRToken]
    ) -> HackRxResponse:
        """
        Convert BillExtractionOutput to HackRxResponse
        
        Args:
            extraction_output: Output from BillExtractor
            all_tokens: All OCR tokens (for page classification)
            
        Returns:
            HackRx formatted response
        """
        try:
            if extraction_output.meta.status != "SUCCESS" or not extraction_output.bill:
                return HackRxResponse(
                    is_success=False,
                    token_usage=self.token_usage,
                    data=HackRxData()
                )
            
            # Group line items by page
            items_by_page = self._group_items_by_page(extraction_output.bill.line_items)
            
            # Group tokens by page for classification
            tokens_by_page = self._group_tokens_by_page(all_tokens)
            
            # Create pagewise line items
            pagewise_items = []
            total_item_count = 0
            
            for page_num in sorted(items_by_page.keys()):
                # Classify page type
                page_tokens = tokens_by_page.get(page_num, [])
                page_type = self.page_classifier.classify_page(page_tokens, page_num)
                
                # Convert line items to bill items
                bill_items = []
                for item in items_by_page[page_num]:
                    bill_item = self._convert_line_item_to_bill_item(item)
                    bill_items.append(bill_item)
                    total_item_count += 1
                
                # Create pagewise entry
                pagewise_items.append(PagewiseLineItem(
                    page_no=str(page_num),
                    page_type=page_type,
                    bill_items=bill_items
                ))
            
            # Create response
            response = HackRxResponse(
                is_success=True,
                token_usage=self.token_usage,
                data=HackRxData(
                    pagewise_line_items=pagewise_items,
                    total_item_count=total_item_count
                )
            )
            
            logger.info(f"Converted to HackRx format: {total_item_count} items across {len(pagewise_items)} pages")
            return response
            
        except Exception as e:
            logger.error(f"Failed to convert to HackRx format: {e}", exc_info=True)
            return HackRxResponse(
                is_success=False,
                token_usage=self.token_usage,
                data=HackRxData()
            )
    
    def _group_items_by_page(self, line_items: List[LineItem]) -> Dict[int, List[LineItem]]:
        """Group line items by page number"""
        items_by_page = defaultdict(list)
        for item in line_items:
            items_by_page[item.page].append(item)
        return dict(items_by_page)
    
    def _group_tokens_by_page(self, tokens: List[OCRToken]) -> Dict[int, List[OCRToken]]:
        """Group tokens by page number"""
        tokens_by_page = defaultdict(list)
        for token in tokens:
            tokens_by_page[token.page].append(token)
        return dict(tokens_by_page)
    
    def _convert_line_item_to_bill_item(self, line_item: LineItem) -> BillItem:
        """
        Convert LineItem to BillItem format
        
        Args:
            line_item: Internal LineItem
            
        Returns:
            HackRx BillItem
        """
        return BillItem(
            item_name=line_item.description,
            item_amount=line_item.amount,
            item_rate=line_item.unit_price if line_item.unit_price is not None else line_item.amount,
            item_quantity=line_item.quantity if line_item.quantity is not None else 1.0
        )
    
    def update_token_usage(self, input_tokens: int, output_tokens: int):
        """
        Update token usage tracking
        
        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
        """
        self.token_usage.input_tokens += input_tokens
        self.token_usage.output_tokens += output_tokens
        self.token_usage.total_tokens = self.token_usage.input_tokens + self.token_usage.output_tokens
