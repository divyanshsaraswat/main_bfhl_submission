"""
Fraud detection and anomaly detection module
Detects arithmetic mismatches, visual inconsistencies, and structural anomalies
"""

from typing import List, Dict, Any, Optional
from src.core.models import OCRToken, LineItem, FraudSignal, FraudSignalType, SubTotal
from config.config import Config
from src.core.utils import (
    bbox_height, bbox_area, calculate_arithmetic_difference_percent,
    extract_number
)


class FraudDetector:
    """Detects fraud and anomalies in bill data"""
    
    def __init__(self):
        self.signals: List[FraudSignal] = []
    
    def detect_all(self, 
                   line_items: List[LineItem],
                   sub_totals: List[SubTotal],
                   final_total_value: float,
                   all_tokens: List[OCRToken]) -> List[FraudSignal]:
        """Run all fraud detection checks"""
        self.signals = []
        
        if Config.ENABLE_ARITHMETIC_CHECK:
            self._check_line_item_arithmetic(line_items)
            self._check_total_reconciliation(line_items, final_total_value)
            self._check_subtotal_logic(sub_totals, final_total_value)
        
        if Config.ENABLE_OCR_CONFIDENCE_CHECK:
            self._check_ocr_confidence(all_tokens)
        
        if Config.ENABLE_FONT_ANALYSIS:
            self._check_font_inconsistencies(all_tokens)
        
        if Config.ENABLE_SEMANTIC_CHECK:
            self._check_semantic_anomalies(line_items, sub_totals, final_total_value)
        
        return self.signals
    
    def _check_line_item_arithmetic(self, line_items: List[LineItem]):
        """Check if qty × unit_price = amount for each line item"""
        for item in line_items:
            if item.quantity is not None and item.unit_price is not None:
                expected_amount = item.quantity * item.unit_price
                diff_percent = calculate_arithmetic_difference_percent(expected_amount, item.amount)
                
                if diff_percent > Config.ARITHMETIC_TOLERANCE_PERCENT:
                    self.signals.append(FraudSignal(
                        type=FraudSignalType.ARITHMETIC_MISMATCH,
                        message=f"Line item arithmetic mismatch: {item.quantity} × {item.unit_price} = {expected_amount:.2f}, but amount is {item.amount:.2f} (diff: {diff_percent:.1f}%)",
                        page=item.page
                    ))
    
    def _check_total_reconciliation(self, line_items: List[LineItem], final_total: float):
        """Check if sum of line items matches final total"""
        line_items_sum = sum(item.amount for item in line_items)
        difference = abs(final_total - line_items_sum)
        
        if difference > Config.TOTAL_RECONCILIATION_TOLERANCE:
            self.signals.append(FraudSignal(
                type=FraudSignalType.ARITHMETIC_MISMATCH,
                message=f"Total reconciliation mismatch: line items sum to {line_items_sum:.2f}, but final total is {final_total:.2f} (diff: {difference:.2f})",
                page=line_items[0].page if line_items else 1
            ))
    
    def _check_subtotal_logic(self, sub_totals: List[SubTotal], final_total: float):
        """Check if any subtotal is greater than final total"""
        for subtotal in sub_totals:
            if subtotal.value > final_total:
                self.signals.append(FraudSignal(
                    type=FraudSignalType.STRUCTURAL_ANOMALY,
                    message=f"Subtotal '{subtotal.label}' ({subtotal.value:.2f}) is greater than final total ({final_total:.2f})",
                    page=subtotal.page
                ))
    
    def _check_ocr_confidence(self, tokens: List[OCRToken]):
        """Check for low OCR confidence tokens"""
        low_confidence_tokens = [
            token for token in tokens 
            if token.confidence < Config.MIN_OCR_CONFIDENCE
        ]
        
        if low_confidence_tokens:
            # Group by page
            by_page = {}
            for token in low_confidence_tokens:
                if token.page not in by_page:
                    by_page[token.page] = []
                by_page[token.page].append(token)
            
            for page, page_tokens in by_page.items():
                self.signals.append(FraudSignal(
                    type=FraudSignalType.OCR_LOW_CONFIDENCE,
                    message=f"Found {len(page_tokens)} tokens with OCR confidence < {Config.MIN_OCR_CONFIDENCE} (lowest: {min(t.confidence for t in page_tokens):.2f})",
                    page=page
                ))
        
        # Check for sharp confidence drops
        self._check_confidence_anomalies(tokens)
    
    def _check_confidence_anomalies(self, tokens: List[OCRToken]):
        """Detect sharp drops in OCR confidence"""
        if len(tokens) < 3:
            return
        
        # Group by page
        by_page = {}
        for token in tokens:
            if token.page not in by_page:
                by_page[token.page] = []
            by_page[token.page].append(token)
        
        for page, page_tokens in by_page.items():
            confidences = [t.confidence for t in page_tokens]
            avg_confidence = sum(confidences) / len(confidences)
            
            # Calculate standard deviation manually
            variance = sum((x - avg_confidence) ** 2 for x in confidences) / len(confidences)
            std_confidence = variance ** 0.5
            
            # Find outliers (more than 2 std deviations below mean)
            for token in page_tokens:
                if token.confidence < (avg_confidence - 2 * std_confidence):
                    self.signals.append(FraudSignal(
                        type=FraudSignalType.OCR_LOW_CONFIDENCE,
                        message=f"Confidence anomaly detected: token '{token.text}' has confidence {token.confidence:.2f}, significantly below page average {avg_confidence:.2f}",
                        page=page
                    ))
    
    def _check_font_inconsistencies(self, tokens: List[OCRToken]):
        """Check for font height and bbox size inconsistencies"""
        if len(tokens) < 2:
            return
        
        # Group by page
        by_page = {}
        for token in tokens:
            if token.page not in by_page:
                by_page[token.page] = []
            by_page[token.page].append(token)
        
        for page, page_tokens in by_page.items():
            heights = [bbox_height(t.bbox) for t in page_tokens]
            areas = [bbox_area(t.bbox) for t in page_tokens]
            
            # Calculate median manually
            sorted_heights = sorted(heights)
            sorted_areas = sorted(areas)
            n_h = len(sorted_heights)
            n_a = len(sorted_areas)
            median_height = sorted_heights[n_h // 2] if n_h % 2 == 1 else (sorted_heights[n_h // 2 - 1] + sorted_heights[n_h // 2]) / 2
            median_area = sorted_areas[n_a // 2] if n_a % 2 == 1 else (sorted_areas[n_a // 2 - 1] + sorted_areas[n_a // 2]) / 2
            
            # Check for outliers
            for token in page_tokens:
                token_height = bbox_height(token.bbox)
                token_area = bbox_area(token.bbox)
                
                # Check height variance
                if median_height > 0:
                    height_ratio = token_height / median_height
                    if height_ratio > Config.FONT_HEIGHT_VARIANCE_THRESHOLD or height_ratio < (1 / Config.FONT_HEIGHT_VARIANCE_THRESHOLD):
                        self.signals.append(FraudSignal(
                            type=FraudSignalType.FONT_INCONSISTENCY,
                            message=f"Font height anomaly: token '{token.text}' has height {token_height:.1f}px, median is {median_height:.1f}px (ratio: {height_ratio:.2f})",
                            page=page
                        ))
                
                # Check area variance (potential overwrite)
                if median_area > 0:
                    area_ratio = token_area / median_area
                    if area_ratio > Config.BBOX_AREA_VARIANCE_THRESHOLD:
                        self.signals.append(FraudSignal(
                            type=FraudSignalType.OVERWRITE_DETECTED,
                            message=f"Potential overwrite detected: token '{token.text}' has unusually large bbox area (ratio: {area_ratio:.2f})",
                            page=page
                        ))
    
    def _check_semantic_anomalies(self, line_items: List[LineItem], 
                                   sub_totals: List[SubTotal], 
                                   final_total: float):
        """Check for semantic inconsistencies"""
        # Check if any line item amount is greater than final total
        for item in line_items:
            if item.amount > final_total:
                self.signals.append(FraudSignal(
                    type=FraudSignalType.STRUCTURAL_ANOMALY,
                    message=f"Line item amount ({item.amount:.2f}) exceeds final total ({final_total:.2f}): {item.description}",
                    page=item.page
                ))
        
        # Check for duplicate line items (potential padding)
        descriptions = [item.description.lower().strip() for item in line_items]
        seen = set()
        for idx, desc in enumerate(descriptions):
            if desc in seen and desc:  # Non-empty duplicates
                self.signals.append(FraudSignal(
                    type=FraudSignalType.STRUCTURAL_ANOMALY,
                    message=f"Duplicate line item detected: '{line_items[idx].description}'",
                    page=line_items[idx].page
                ))
            seen.add(desc)
    
    def get_signals(self) -> List[FraudSignal]:
        """Get all detected fraud signals"""
        return self.signals
