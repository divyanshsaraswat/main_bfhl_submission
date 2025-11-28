# Project Structure

```
BFHL/
├── .env.example              # Environment variables template
├── .gitignore               # Git ignore rules
├── Dockerfile               # Docker container configuration
├── README.md                # Main documentation
├── DEPLOYMENT.md            # Deployment guide
├── PROJECT_OVERVIEW.md      # Project overview
├── requirements.txt         # Python dependencies
├── run.py                   # Server launcher script
├── test_hackrx_api.py      # HackRx API test script
│
├── config/                  # Configuration
│   ├── __init__.py
│   └── config.py           # Configuration settings
│
├── src/                    # Source code
│   ├── __init__.py
│   ├── api/               # API layer
│   │   ├── __init__.py
│   │   ├── main.py        # FastAPI application
│   │   └── hackrx_models.py  # HackRx API schemas
│   │
│   └── core/              # Core extraction logic
│       ├── __init__.py
│       ├── bill_extractor.py    # Main extraction engine
│       ├── fraud_detector.py    # Fraud detection
│       ├── hackrx_adapter.py    # Format conversion
│       ├── models.py            # Internal data models
│       ├── ocr_processor.py     # Document download & OCR
│       ├── page_classifier.py   # Page type classification
│       ├── table_parser.py      # Table structure parsing
│       └── utils.py             # Utility functions
│
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_extractor.py  # Unit tests
│   └── test_*.py          # Additional tests
│
├── test_data/             # Sample test data
│   ├── sample_bill.json
│   └── fraud_bill.json
│
├── docs/                  # Additional documentation
│   └── README.md
│
└── venv/                  # Virtual environment (not in git)
```

## Key Files

### Root Level
- **run.py**: Main entry point to start the server
- **test_hackrx_api.py**: Test script for HackRx API endpoint
- **requirements.txt**: All Python dependencies
- **Dockerfile**: For containerized deployment
- **README.md**: Complete project documentation
- **DEPLOYMENT.md**: Deployment instructions

### Source Code (src/)
- **src/api/main.py**: FastAPI application with `/extract-bill-data` endpoint
- **src/api/hackrx_models.py**: Pydantic models for HackRx API
- **src/core/ocr_processor.py**: Handles document download and OCR
- **src/core/page_classifier.py**: Classifies pages (Bill Detail/Final Bill/Pharmacy)
- **src/core/bill_extractor.py**: Main extraction logic
- **src/core/hackrx_adapter.py**: Converts internal format to HackRx format
- **src/core/table_parser.py**: Parses table structures
- **src/core/fraud_detector.py**: Detects fraud signals
- **src/core/models.py**: Internal data models
- **src/core/utils.py**: Helper functions

### Configuration (config/)
- **config/config.py**: All configuration parameters

### Tests (tests/)
- **tests/test_extractor.py**: Unit tests for extraction logic

## File Organization Principles

1. **No duplicate files**: All code files exist only once in their proper location
2. **Separation of concerns**: API, core logic, and config are separated
3. **Clear hierarchy**: Easy to navigate and understand
4. **Test isolation**: Tests are in dedicated directory
5. **Documentation at root**: Easy to find README and guides
