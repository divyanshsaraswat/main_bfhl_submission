"""
HackRx API Data Models
Defines Pydantic schemas matching the hackathon API specification
"""

from typing import List, Literal
from pydantic import BaseModel, Field


class DocumentInput(BaseModel):
    """Input schema for document URL"""
    document: str = Field(..., description="URL to the document image")


class BillItem(BaseModel):
    """Individual line item from bill"""
    item_name: str = Field(..., description="Exactly as mentioned in the bill")
    item_amount: float = Field(..., description="Net amount post discounts")
    item_rate: float = Field(..., description="Rate per unit")
    item_quantity: float = Field(..., description="Quantity")


class PagewiseLineItem(BaseModel):
    """Line items grouped by page"""
    page_no: str = Field(..., description="Page number as string")
    page_type: Literal["Bill Detail", "Final Bill", "Pharmacy"] = Field(
        ..., description="Type of page"
    )
    bill_items: List[BillItem] = Field(default_factory=list)


class TokenUsage(BaseModel):
    """LLM token usage tracking"""
    total_tokens: int = Field(0, description="Cumulative tokens from all LLM calls")
    input_tokens: int = Field(0, description="Cumulative input tokens")
    output_tokens: int = Field(0, description="Cumulative output tokens")


class HackRxData(BaseModel):
    """Main data container"""
    pagewise_line_items: List[PagewiseLineItem] = Field(default_factory=list)
    total_item_count: int = Field(0, description="Count of items across all pages")


class HackRxResponse(BaseModel):
    """Complete API response"""
    is_success: bool = Field(..., description="True if status 200 and valid schema")
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    data: HackRxData = Field(default_factory=HackRxData)


class ErrorResponse(BaseModel):
    """Error response schema"""
    is_success: bool = Field(False)
    message: str = Field(..., description="Error message")
