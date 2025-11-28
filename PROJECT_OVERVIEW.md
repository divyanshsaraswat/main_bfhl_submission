# Bill Extraction & Validation Agent

A complete, production-grade system for extracting structured data from multi-page, multi-format medical bills.

## Project Structure

```
BFHL/
├── src/
│   ├── core/          - Core extraction logic (models, extractors, parsers)
│   └── api/           - FastAPI application
├── config/            - Configuration and settings
├── tests/             - Test suite
├── test_data/         - Sample test data
├── docs/              - Full documentation
└── requirements.txt   - Python dependencies
```

## Quick Start

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Run server**: `cd src/api && uvicorn main:app --reload`
3. **Access docs**: http://localhost:8000/docs
4. **Run tests**: `python tests/test_extractor.py`

## Key Features

- ✅ Intelligent table parsing and column detection
- ✅ Line item extraction with confidence scoring
- ✅ Fraud detection (arithmetic, OCR, structural anomalies)
- ✅ Multi-page bill support
- ✅ REST API with FastAPI
- ✅ Comprehensive test suite

## Documentation

See `docs/README.md` for complete documentation.

## Version

1.0.0 - Production Ready
