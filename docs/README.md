# Bill Extraction & Validation Agent

A production-grade system for extracting structured data from multi-page, multi-format medical bills with built-in fraud detection capabilities.

## Features

✅ **Intelligent Table Parsing** - Automatic detection of table structure, headers, and columns  
✅ **Line Item Extraction** - Extract description, quantity, unit price, and amount  
✅ **Total Detection** - Identify subtotals and final totals with priority-based matching  
✅ **Fraud Detection** - Detect arithmetic mismatches, OCR anomalies, and structural inconsistencies  
✅ **Confidence Scoring** - Per-item and overall confidence metrics  
✅ **Multi-page Support** - Process bills spanning multiple pages  
✅ **Robust OCR Handling** - Handle noisy, rotated, or imperfect OCR output  
✅ **REST API** - FastAPI-based endpoints for easy integration  

## Architecture

```
bill_extractor.py      - Main extraction orchestrator
table_parser.py        - Table structure understanding
fraud_detector.py      - Fraud and anomaly detection
models.py              - Pydantic data models
config.py              - Configuration and thresholds
utils.py               - Utility functions
main.py                - FastAPI application
```

## Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

```bash
# Clone or navigate to project directory
cd C:\Users\mgpsk\Documents\BFHL

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Start the API Server

```bash
uvicorn main:app --reload
```

The server will start at `http://localhost:8000`

### 2. Access API Documentation

Open your browser and navigate to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Test with Sample Data

```bash
# Run the test suite
python test_extractor.py
```

## API Usage

### Extract Bill Data

**Endpoint**: `POST /extract`

**Input**: OCR tokens in JSON format

```json
{
  "tokens": [
    {
      "text": "Consultation",
      "bbox": [50, 250, 180, 270],
      "page": 1,
      "confidence": 0.92
    },
    ...
  ],
  "total_pages": 1
}
```

**Output**: Structured bill data with fraud signals

```json
{
  "meta": {
    "status": "SUCCESS",
    "pages_processed": 1,
    "model_confidence": 0.94,
    "processing_notes": []
  },
  "bill": {
    "line_items": [
      {
        "description": "Consultation",
        "quantity": 1,
        "unit_price": 500,
        "amount": 500,
        "page": 1,
        "row_index": 2,
        "confidence": 0.93
      }
    ],
    "sub_totals": [],
    "final_total": {
      "value": 2350,
      "currency": "INR",
      "page": 1
    },
    "aggregates": {
      "line_items_total": 2350,
      "detected_final_total": 2350,
      "difference": 0,
      "reconciliation_status": "MATCHED"
    },
    "fraud_signals": []
  }
}
```

### Example with cURL

```bash
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: application/json" \
  -d @test_data/sample_bill.json
```

### Example with Python

```python
import requests
import json

# Load test data
with open('test_data/sample_bill.json', 'r') as f:
    data = json.load(f)

# Make request
response = requests.post('http://localhost:8000/extract', json=data)
result = response.json()

print(f"Status: {result['meta']['status']}")
print(f"Line items: {len(result['bill']['line_items'])}")
print(f"Total: {result['bill']['final_total']['value']}")
```

## Input Specification

### OCR Token Format

Each token must include:

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | The OCR-recognized text |
| `bbox` | array[4] | Bounding box `[x1, y1, x2, y2]` |
| `page` | integer | Page number (1-indexed) |
| `confidence` | float | OCR confidence (0.0 - 1.0) |

### Example Token

```json
{
  "text": "INJECTION",
  "bbox": [100, 250, 200, 270],
  "page": 2,
  "confidence": 0.93
}
```

## Output Specification

### Line Item

```json
{
  "description": "Blood Test",
  "quantity": 2,
  "unit_price": 300,
  "amount": 600,
  "page": 1,
  "row_index": 3,
  "confidence": 0.94
}
```

### Fraud Signal Types

- `ARITHMETIC_MISMATCH` - qty × rate ≠ amount
- `FONT_INCONSISTENCY` - Unusual font height variations
- `OVERWRITE_DETECTED` - Suspicious bbox patterns
- `OCR_LOW_CONFIDENCE` - Low OCR confidence scores
- `STRUCTURAL_ANOMALY` - Semantic inconsistencies

## Configuration

Edit `config.py` to customize:

```python
# OCR Confidence Thresholds
MIN_OCR_CONFIDENCE = 0.60
LOW_CONFIDENCE_THRESHOLD = 0.70

# Arithmetic Validation
ARITHMETIC_TOLERANCE_PERCENT = 3.0
TOTAL_RECONCILIATION_TOLERANCE = 5.0

# Table Parsing
Y_COORDINATE_TOLERANCE = 5.0
MIN_COLUMN_GAP = 20.0
```

## Testing

### Run All Tests

```bash
python test_extractor.py
```

### Test Individual Components

```python
from test_extractor import (
    test_sample_bill_extraction,
    test_fraud_detection,
    test_table_parser
)

# Test specific functionality
test_sample_bill_extraction()
test_fraud_detection()
```

### Sample Test Data

- `test_data/sample_bill.json` - Valid medical bill
- `test_data/fraud_bill.json` - Bill with arithmetic errors

## Fraud Detection

The system automatically detects:

### Arithmetic Anomalies
- Line item calculation errors (qty × rate ≠ amount)
- Total reconciliation mismatches
- Subtotal logic violations

### Visual Inconsistencies
- Font height variations (potential tampering)
- Unusual bounding box sizes (potential overwrites)
- Whitening regions

### OCR Anomalies
- Low confidence tokens (< 0.60)
- Sharp confidence drops
- Statistical outliers

### Semantic Issues
- Line items exceeding final total
- Duplicate line items
- Subtotals greater than final total

## Error Handling

### Failed Extraction

```json
{
  "meta": {
    "status": "FAILED",
    "reason": "UNREADABLE_OR_INVALID_DOCUMENT"
  }
}
```

### Common Failure Reasons

- `UNREADABLE_OR_INVALID_DOCUMENT` - Document doesn't resemble a bill
- `No OCR tokens provided` - Empty input
- `Extraction error: ...` - Processing exception

## Performance

- **Average processing time**: < 500ms for single-page bills
- **Memory usage**: ~50MB per request
- **Concurrent requests**: Supports multiple simultaneous requests

## Deployment

### Production Deployment

```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information |
| `/health` | GET | Health check |
| `/extract` | POST | Main extraction endpoint |
| `/extract-json` | POST | Alternative JSON endpoint |
| `/validate-input` | POST | Validate input format |

## Troubleshooting

### Issue: Low confidence scores

**Solution**: Check OCR quality, adjust `MIN_OCR_CONFIDENCE` threshold

### Issue: Missing line items

**Solution**: Verify table structure, check column mapping in logs

### Issue: Incorrect totals

**Solution**: Review total keyword configuration in `config.py`

### Issue: Too many fraud signals

**Solution**: Adjust tolerance thresholds in `config.py`

## License

MIT License

## Support

For issues or questions, please contact the development team.

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-27
