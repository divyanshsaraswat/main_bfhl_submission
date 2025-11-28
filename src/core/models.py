"""
Data models for Bill Extraction & Validation Agent
Defines Pydantic schemas for input/output validation
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


class OCRToken(BaseModel):
    """Single OCR token with bounding box and metadata"""
    text: str
    bbox: List[float] = Field(..., description="[x1, y1, x2, y2]")
    page: int = Field(..., ge=1)
    confidence: float = Field(..., ge=0.0, le=1.0)


class OCRInput(BaseModel):
    """Input schema for OCR tokens"""
    tokens: List[OCRToken]
    total_pages: Optional[int] = None
    metadata: Optional[dict] = None


class LineItem(BaseModel):
    """Extracted line item from bill"""
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: float
    page: int
    row_index: int
    confidence: float = Field(..., ge=0.0, le=1.0)


class SubTotal(BaseModel):
    """Subtotal entry"""
    label: str
    value: float
    page: int


class FinalTotal(BaseModel):
    """Final total amount"""
    value: float
    currency: str = "INR"
    page: int


class Aggregates(BaseModel):
    """Aggregated calculations and reconciliation"""
    line_items_total: float
    detected_final_total: float
    difference: float
    reconciliation_status: Literal["MATCHED", "MISMATCH"]


class FraudSignalType(str, Enum):
    """Types of fraud signals"""
    ARITHMETIC_MISMATCH = "ARITHMETIC_MISMATCH"
    FONT_INCONSISTENCY = "FONT_INCONSISTENCY"
    OVERWRITE_DETECTED = "OVERWRITE_DETECTED"
    OCR_LOW_CONFIDENCE = "OCR_LOW_CONFIDENCE"
    STRUCTURAL_ANOMALY = "STRUCTURAL_ANOMALY"


class FraudSignal(BaseModel):
    """Fraud or anomaly signal"""
    type: FraudSignalType
    message: str
    page: int


class BillData(BaseModel):
    """Extracted bill data"""
    line_items: List[LineItem]
    sub_totals: List[SubTotal]
    final_total: FinalTotal
    aggregates: Aggregates
    fraud_signals: List[FraudSignal]


class MetaData(BaseModel):
    """Processing metadata"""
    status: Literal["SUCCESS", "FAILED"]
    pages_processed: Optional[int] = None
    model_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    processing_notes: List[str] = Field(default_factory=list)
    reason: Optional[str] = None  # For FAILED status


class BillExtractionOutput(BaseModel):
    """Complete output schema"""
    meta: MetaData
    bill: Optional[BillData] = None
