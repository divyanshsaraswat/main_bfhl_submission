"""
Main Bill Extraction Engine
Orchestrates table parsing, line item extraction, total detection, and fraud detection
"""

from typing import List, Optional, Dict, Any
from src.core.models import (
    OCRToken, OCRInput, LineItem, SubTotal, FinalTotal, 
    Aggregates, BillData, MetaData, BillExtractionOutput
)
from src.core.table_parser import TableParser, TableRow
from src.core.fraud_detector import FraudDetector
from config.config import Config
from src.core.utils import (
    extract_number, normalize_text, find_keyword_in_tokens,
    calculate_confidence, merge_tokens_text, is_numeric_text
)


class BillExtractor:
    """Main extraction engine for processing bills"""
    
    def __init__(self):
        self.tokens: List[OCRToken] = []
        self.parser: Optional[TableParser] = None
        self.fraud_detector = FraudDetector()
        self.processing_notes: List[str] = []
    
    def extract(self, ocr_input: OCRInput) -> BillExtractionOutput:
        """Main extraction method"""
        try:
            self.tokens = ocr_input.tokens
            self.processing_notes = []
            
            # Validate input
            if not self.tokens:
                return self._failed_response("No OCR tokens provided")
            
            # Check if document is readable
            if not self._is_readable():
                return self._failed_response("UNREADABLE_OR_INVALID_DOCUMENT")
            
            # Parse table structure
            self.parser = TableParser(self.tokens)
            self.parser.parse()
            
            # Extract components
            line_items = self._extract_line_items()
            sub_totals = self._extract_subtotals()
            final_total = self._extract_final_total()
            
            # Calculate aggregates
            aggregates = self._calculate_aggregates(line_items, final_total)
            
            # Detect fraud
            fraud_signals = self.fraud_detector.detect_all(
                line_items, sub_totals, final_total.value, self.tokens
            )
            
            # Calculate overall confidence
            model_confidence = self._calculate_model_confidence(line_items)
            
            # Build response
            bill_data = BillData(
                line_items=line_items,
                sub_totals=sub_totals,
                final_total=final_total,
                aggregates=aggregates,
                fraud_signals=fraud_signals
            )
            
            meta = MetaData(
                status="SUCCESS",
                pages_processed=self._get_page_count(),
                model_confidence=model_confidence,
                processing_notes=self.processing_notes
            )
            
            return BillExtractionOutput(meta=meta, bill=bill_data)
        
        except Exception as e:
            return self._failed_response(f"Extraction error: {str(e)}")
    
    def _is_readable(self) -> bool:
        """Check if document appears to be a readable bill"""
        # Check if we have minimum number of tokens
        if len(self.tokens) < 10:
            return False
        
        # Check average OCR confidence
        confidences = [t.confidence for t in self.tokens]
        avg_confidence = sum(confidences) / len(confidences)
        if avg_confidence < 0.3:
            return False
        
        # Check if we have some numeric content (bills should have numbers)
        numeric_count = sum(1 for t in self.tokens if is_numeric_text(t.text))
        if numeric_count < 3:
            return False
        
        return True
    
    def _extract_line_items(self) -> List[LineItem]:
        """Extract line items from parsed table"""
        line_items = []
        
        if not self.parser:
            return line_items
        
        data_rows = self.parser.get_data_rows()
        
        for row in data_rows:
            row_data = self.parser.extract_row_data(row)
            
            # Skip if no description or amount
            if not row_data['description'] or not row_data['amount']:
                continue
            
            # Check if this is a total/subtotal row (skip it)
            desc_lower = normalize_text(row_data['description'])
            if any(keyword in desc_lower for keyword in Config.TOTAL_KEYWORDS + Config.SUBTOTAL_KEYWORDS):
                continue
            
            # Parse numeric values
            amount = extract_number(row_data['amount'])
            if amount is None:
                continue
            
            quantity = None
            if row_data['quantity']:
                quantity = extract_number(row_data['quantity'])
            
            unit_price = None
            if row_data['unit_price']:
                unit_price = extract_number(row_data['unit_price'])
            
            # Calculate confidence
            token_confidences = [t.confidence for t in row_data['tokens']]
            confidence = calculate_confidence(token_confidences)
            
            line_item = LineItem(
                description=row_data['description'].strip(),
                quantity=quantity,
                unit_price=unit_price,
                amount=amount,
                page=row_data['page'],
                row_index=row_data['row_index'],
                confidence=confidence
            )
            
            line_items.append(line_item)
        
        if not line_items:
            self.processing_notes.append("No line items extracted from table")
        
        return line_items
    
    def _extract_subtotals(self) -> List[SubTotal]:
        """Extract subtotals from document"""
        subtotals = []
        
        if not self.parser:
            return subtotals
        
        # Look through all rows for subtotal keywords
        for row in self.parser.rows:
            row_text = merge_tokens_text(row.tokens)
            row_text_lower = normalize_text(row_text)
            
            # Check if row contains subtotal keyword
            matched_keyword = None
            for keyword in Config.SUBTOTAL_KEYWORDS:
                if keyword in row_text_lower:
                    matched_keyword = keyword
                    break
            
            if matched_keyword:
                # Try to extract value from this row or nearby tokens
                value = self._extract_value_from_row(row)
                
                if value is not None:
                    subtotals.append(SubTotal(
                        label=row_text.strip(),
                        value=value,
                        page=row.page
                    ))
        
        return subtotals
    
    def _extract_final_total(self) -> FinalTotal:
        """Extract final total from document"""
        if not self.parser:
            # Fallback: try to find any total
            return self._extract_total_fallback()
        
        # Search for total keywords in priority order
        best_match = None
        best_priority = -1
        
        for row in self.parser.rows:
            row_text = merge_tokens_text(row.tokens)
            row_text_lower = normalize_text(row_text)
            
            # Check against total keywords
            for priority, keyword in enumerate(Config.TOTAL_KEYWORDS):
                if keyword in row_text_lower:
                    value = self._extract_value_from_row(row)
                    
                    if value is not None:
                        # Higher priority = lower index (grand total > total)
                        if best_match is None or priority < best_priority:
                            best_match = FinalTotal(
                                value=value,
                                currency="INR",
                                page=row.page
                            )
                            best_priority = priority
        
        if best_match:
            return best_match
        
        # Fallback: use sum of line items
        self.processing_notes.append("Final total not found in document, using sum of line items")
        return self._extract_total_fallback()
    
    def _extract_total_fallback(self) -> FinalTotal:
        """Fallback method to extract total"""
        # Find the largest numeric value in the document
        max_value = 0.0
        max_page = 1
        
        for token in self.tokens:
            value = extract_number(token.text)
            if value and value > max_value:
                max_value = value
                max_page = token.page
        
        return FinalTotal(
            value=max_value,
            currency="INR",
            page=max_page
        )
    
    def _extract_value_from_row(self, row: TableRow) -> Optional[float]:
        """Extract numeric value from a row (usually rightmost column)"""
        # Try rightmost column first
        if row.columns:
            max_col_idx = max(row.columns.keys())
            rightmost_text = row.get_column_text(max_col_idx)
            value = extract_number(rightmost_text)
            if value is not None:
                return value
        
        # Try all tokens in row
        for token in reversed(row.tokens):  # Right to left
            value = extract_number(token.text)
            if value is not None:
                return value
        
        return None
    
    def _calculate_aggregates(self, line_items: List[LineItem], 
                             final_total: FinalTotal) -> Aggregates:
        """Calculate aggregate values and reconciliation"""
        line_items_total = sum(item.amount for item in line_items)
        detected_final_total = final_total.value
        difference = detected_final_total - line_items_total
        
        # Determine reconciliation status
        if abs(difference) <= Config.TOTAL_RECONCILIATION_TOLERANCE:
            status = "MATCHED"
        else:
            status = "MISMATCH"
        
        return Aggregates(
            line_items_total=line_items_total,
            detected_final_total=detected_final_total,
            difference=difference,
            reconciliation_status=status
        )
    
    def _calculate_model_confidence(self, line_items: List[LineItem]) -> float:
        """Calculate overall model confidence"""
        if not line_items:
            return 0.0
        
        confidences = [item.confidence for item in line_items]
        return sum(confidences) / len(confidences)
    
    def _get_page_count(self) -> int:
        """Get total number of pages processed"""
        if not self.tokens:
            return 0
        return max(token.page for token in self.tokens)
    
    def _failed_response(self, reason: str) -> BillExtractionOutput:
        """Create failed response"""
        meta = MetaData(
            status="FAILED",
            reason=reason
        )
        return BillExtractionOutput(meta=meta, bill=None)
