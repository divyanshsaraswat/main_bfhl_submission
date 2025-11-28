"""
Configuration settings for Bill Extraction & Validation Agent
"""

from typing import Dict, Any


class Config:
    """Configuration parameters for bill extraction"""
    
    # OCR Confidence Thresholds
    MIN_OCR_CONFIDENCE = 0.60
    LOW_CONFIDENCE_THRESHOLD = 0.70
    
    # Arithmetic Validation
    ARITHMETIC_TOLERANCE_PERCENT = 3.0  # 3% tolerance for qty × rate = amount
    TOTAL_RECONCILIATION_TOLERANCE = 5.0  # Absolute tolerance for total reconciliation
    
    # Spatial Clustering (for table parsing)
    Y_COORDINATE_TOLERANCE = 5.0  # pixels - for grouping words into lines
    X_COORDINATE_TOLERANCE = 10.0  # pixels - for column detection
    MIN_COLUMN_GAP = 20.0  # pixels - minimum gap between columns
    
    # Font/Visual Anomaly Detection
    FONT_HEIGHT_VARIANCE_THRESHOLD = 2.0  # multiplier - flag if height differs by 2x
    BBOX_AREA_VARIANCE_THRESHOLD = 3.0  # multiplier - flag suspicious bbox sizes
    
    # Confidence Scoring Weights
    CONFIDENCE_WEIGHTS = {
        'ocr': 0.4,
        'structural': 0.3,
        'column_mapping': 0.3
    }
    
    # Table Header Keywords (case-insensitive)
    HEADER_KEYWORDS = {
        'description': ['particulars', 'description', 'item', 'service', 'procedure'],
        'quantity': ['qty', 'quantity', 'count', 'no', 'units'],
        'unit_price': ['rate', 'price', 'unit price', 'cost', 'unit cost'],
        'amount': ['amount', 'total', 'value', 'charges']
    }
    
    # Total Keywords (case-insensitive, ordered by priority)
    TOTAL_KEYWORDS = [
        'grand total',
        'net payable',
        'amount to pay',
        'total amount',
        'final total',
        'total payable',
        'total'
    ]
    
    # Subtotal Keywords
    SUBTOTAL_KEYWORDS = [
        'subtotal',
        'sub total',
        'room charges total',
        'consultation charges',
        'pharmacy charges',
        'lab charges',
        'procedure charges'
    ]
    
    # Currency Patterns
    CURRENCY_SYMBOLS = ['₹', 'Rs', 'Rs.', 'INR']
    
    # Fraud Detection Settings
    ENABLE_FONT_ANALYSIS = True
    ENABLE_ARITHMETIC_CHECK = True
    ENABLE_SEMANTIC_CHECK = True
    ENABLE_OCR_CONFIDENCE_CHECK = True
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }
