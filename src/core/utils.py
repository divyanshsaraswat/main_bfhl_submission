"""
Utility functions for Bill Extraction & Validation Agent
"""

import re
from typing import List, Tuple, Optional, Dict, Any
from collections import defaultdict
from src.core.models import OCRToken


def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    return text.strip().lower()


def extract_number(text: str) -> Optional[float]:
    """Extract numeric value from text string"""
    # Remove currency symbols and commas
    cleaned = re.sub(r'[₹Rs.,\s]', '', text)
    
    # Try to extract number
    match = re.search(r'-?\d+\.?\d*', cleaned)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def bbox_center(bbox: List[float]) -> Tuple[float, float]:
    """Calculate center point of bounding box"""
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def bbox_area(bbox: List[float]) -> float:
    """Calculate area of bounding box"""
    x1, y1, x2, y2 = bbox
    return (x2 - x1) * (y2 - y1)


def bbox_height(bbox: List[float]) -> float:
    """Calculate height of bounding box"""
    return bbox[3] - bbox[1]


def bbox_width(bbox: List[float]) -> float:
    """Calculate width of bounding box"""
    return bbox[2] - bbox[0]


def bbox_overlap_y(bbox1: List[float], bbox2: List[float]) -> bool:
    """Check if two bounding boxes overlap vertically"""
    y1_min, y1_max = bbox1[1], bbox1[3]
    y2_min, y2_max = bbox2[1], bbox2[3]
    
    return not (y1_max < y2_min or y2_max < y1_min)


def group_by_y_coordinate(tokens: List[OCRToken], tolerance: float = 5.0) -> List[List[OCRToken]]:
    """Group tokens into lines based on y-coordinate proximity"""
    if not tokens:
        return []
    
    # Sort tokens by y-coordinate (top to bottom)
    sorted_tokens = sorted(tokens, key=lambda t: t.bbox[1])
    
    lines = []
    current_line = [sorted_tokens[0]]
    current_y = sorted_tokens[0].bbox[1]
    
    for token in sorted_tokens[1:]:
        token_y = token.bbox[1]
        
        # Check if token belongs to current line
        if abs(token_y - current_y) <= tolerance:
            current_line.append(token)
        else:
            # Sort current line by x-coordinate (left to right)
            current_line.sort(key=lambda t: t.bbox[0])
            lines.append(current_line)
            
            # Start new line
            current_line = [token]
            current_y = token_y
    
    # Add last line
    if current_line:
        current_line.sort(key=lambda t: t.bbox[0])
        lines.append(current_line)
    
    return lines


def detect_columns(tokens: List[OCRToken], min_gap: float = 20.0) -> List[Tuple[float, float]]:
    """Detect column boundaries based on x-coordinates"""
    if not tokens:
        return []
    
    # Get all x-coordinates
    x_coords = []
    for token in tokens:
        x_coords.extend([token.bbox[0], token.bbox[2]])
    
    x_coords = sorted(set(x_coords))
    
    # Find gaps
    columns = []
    current_start = x_coords[0]
    
    for i in range(1, len(x_coords)):
        gap = x_coords[i] - x_coords[i-1]
        if gap > min_gap:
            columns.append((current_start, x_coords[i-1]))
            current_start = x_coords[i]
    
    # Add last column
    if x_coords:
        columns.append((current_start, x_coords[-1]))
    
    return columns


def assign_token_to_column(token: OCRToken, columns: List[Tuple[float, float]]) -> int:
    """Assign token to a column based on its x-coordinate"""
    token_center_x = (token.bbox[0] + token.bbox[2]) / 2
    
    for idx, (col_start, col_end) in enumerate(columns):
        if col_start <= token_center_x <= col_end:
            return idx
    
    # If not in any column, assign to nearest
    distances = [abs(token_center_x - (col_start + col_end) / 2) 
                 for col_start, col_end in columns]
    return distances.index(min(distances))


def calculate_confidence(ocr_confidences: List[float], 
                        structural_certainty: float = 1.0,
                        column_certainty: float = 1.0) -> float:
    """Calculate overall confidence score"""
    if not ocr_confidences:
        return 0.0
    
    ocr_conf = sum(ocr_confidences) / len(ocr_confidences)
    
    # Weighted average
    weights = [0.4, 0.3, 0.3]  # OCR, structural, column
    total = (ocr_conf * weights[0] + 
             structural_certainty * weights[1] + 
             column_certainty * weights[2])
    
    return min(1.0, max(0.0, total))


def is_numeric_text(text: str) -> bool:
    """Check if text is primarily numeric"""
    cleaned = re.sub(r'[₹Rs.,\s-]', '', text)
    return bool(re.match(r'^\d+\.?\d*$', cleaned))


def merge_tokens_text(tokens: List[OCRToken], separator: str = ' ') -> str:
    """Merge multiple tokens into single text string"""
    return separator.join(token.text for token in tokens)


def find_keyword_in_tokens(tokens: List[OCRToken], keywords: List[str]) -> Optional[OCRToken]:
    """Find first token matching any of the keywords (case-insensitive)"""
    normalized_keywords = [normalize_text(kw) for kw in keywords]
    
    for token in tokens:
        normalized_text = normalize_text(token.text)
        for keyword in normalized_keywords:
            if keyword in normalized_text or normalized_text in keyword:
                return token
    
    return None


def calculate_arithmetic_difference_percent(expected: float, actual: float) -> float:
    """Calculate percentage difference between expected and actual values"""
    if expected == 0:
        return 100.0 if actual != 0 else 0.0
    
    return abs((actual - expected) / expected) * 100


def tokens_to_dict(tokens: List[OCRToken]) -> List[Dict[str, Any]]:
    """Convert list of OCRToken objects to list of dictionaries"""
    return [token.model_dump() for token in tokens]
