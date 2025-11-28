"""
Table parsing and layout understanding module
Handles word-to-line grouping, column detection, and table structure extraction
"""

from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.models import OCRToken
from src.core.utils import (
    group_by_y_coordinate, detect_columns, assign_token_to_column,
    normalize_text, merge_tokens_text, find_keyword_in_tokens
)
from config.config import Config


class TableRow:
    """Represents a single row in a table"""
    
    def __init__(self, tokens: List[OCRToken], page: int, row_index: int):
        self.tokens = tokens
        self.page = page
        self.row_index = row_index
        self.columns: Dict[int, List[OCRToken]] = {}
    
    def assign_columns(self, column_boundaries: List[Tuple[float, float]]):
        """Assign tokens to columns"""
        self.columns = defaultdict(list)
        for token in self.tokens:
            col_idx = assign_token_to_column(token, column_boundaries)
            self.columns[col_idx].append(token)
    
    def get_column_text(self, col_idx: int) -> str:
        """Get merged text for a specific column"""
        if col_idx not in self.columns:
            return ""
        return merge_tokens_text(self.columns[col_idx])
    
    def get_column_tokens(self, col_idx: int) -> List[OCRToken]:
        """Get tokens for a specific column"""
        return self.columns.get(col_idx, [])


class TableParser:
    """Parses OCR tokens into structured table format"""
    
    def __init__(self, tokens: List[OCRToken]):
        self.tokens = tokens
        self.rows: List[TableRow] = []
        self.column_boundaries: List[Tuple[float, float]] = []
        self.column_mapping: Dict[str, int] = {}  # Maps field type to column index
        self.header_row_idx: Optional[int] = None
    
    def parse(self) -> List[TableRow]:
        """Main parsing method"""
        # Group tokens by page
        tokens_by_page = self._group_by_page()
        
        # Process each page
        all_rows = []
        global_row_idx = 0
        
        for page, page_tokens in sorted(tokens_by_page.items()):
            # Group tokens into lines
            lines = group_by_y_coordinate(page_tokens, Config.Y_COORDINATE_TOLERANCE)
            
            # Detect columns for this page
            page_columns = detect_columns(page_tokens, Config.MIN_COLUMN_GAP)
            
            if not self.column_boundaries:
                self.column_boundaries = page_columns
            
            # Create rows
            for line_tokens in lines:
                row = TableRow(line_tokens, page, global_row_idx)
                row.assign_columns(self.column_boundaries)
                all_rows.append(row)
                global_row_idx += 1
        
        self.rows = all_rows
        
        # Detect headers and map columns
        self._detect_headers()
        self._map_columns()
        
        return self.rows
    
    def _group_by_page(self) -> Dict[int, List[OCRToken]]:
        """Group tokens by page number"""
        by_page = defaultdict(list)
        for token in self.tokens:
            by_page[token.page].append(token)
        return by_page
    
    def _detect_headers(self):
        """Detect header row based on keywords"""
        for idx, row in enumerate(self.rows):
            # Check if row contains header keywords
            row_text = merge_tokens_text(row.tokens).lower()
            
            header_found = False
            for field_type, keywords in Config.HEADER_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in row_text:
                        header_found = True
                        break
                if header_found:
                    break
            
            if header_found:
                self.header_row_idx = idx
                break
    
    def _map_columns(self):
        """Map column indices to field types (description, quantity, unit_price, amount)"""
        if self.header_row_idx is None:
            # No header found, use heuristics
            self._map_columns_heuristic()
            return
        
        header_row = self.rows[self.header_row_idx]
        
        # Map each field type to column
        for field_type, keywords in Config.HEADER_KEYWORDS.items():
            for col_idx in header_row.columns.keys():
                col_text = normalize_text(header_row.get_column_text(col_idx))
                
                for keyword in keywords:
                    if keyword in col_text or col_text in keyword:
                        self.column_mapping[field_type] = col_idx
                        break
                
                if field_type in self.column_mapping:
                    break
    
    def _map_columns_heuristic(self):
        """Map columns using heuristics when no header is found"""
        if not self.rows or not self.column_boundaries:
            return
        
        num_columns = len(self.column_boundaries)
        
        # Common patterns:
        # - Description is usually the leftmost, widest column
        # - Amount is usually the rightmost column
        # - Quantity and unit_price are in the middle
        
        if num_columns >= 4:
            self.column_mapping = {
                'description': 0,
                'quantity': 1,
                'unit_price': 2,
                'amount': 3
            }
        elif num_columns == 3:
            self.column_mapping = {
                'description': 0,
                'quantity': 1,
                'amount': 2
            }
        elif num_columns == 2:
            self.column_mapping = {
                'description': 0,
                'amount': 1
            }
        else:
            # Single column or too many columns - treat as description
            self.column_mapping = {'description': 0}
    
    def get_data_rows(self) -> List[TableRow]:
        """Get data rows (excluding header)"""
        if self.header_row_idx is None:
            return self.rows
        
        return self.rows[self.header_row_idx + 1:]
    
    def get_column_index(self, field_type: str) -> Optional[int]:
        """Get column index for a field type"""
        return self.column_mapping.get(field_type)
    
    def extract_row_data(self, row: TableRow) -> Dict[str, Any]:
        """Extract structured data from a row"""
        data = {
            'description': '',
            'quantity': None,
            'unit_price': None,
            'amount': None,
            'page': row.page,
            'row_index': row.row_index,
            'tokens': row.tokens
        }
        
        # Extract each field
        for field_type in ['description', 'quantity', 'unit_price', 'amount']:
            col_idx = self.get_column_index(field_type)
            if col_idx is not None:
                text = row.get_column_text(col_idx)
                data[field_type] = text
        
        return data
