"""
Unit tests for Bill Extraction & Validation Agent
"""

import json
from pathlib import Path
from models import OCRInput, OCRToken
from bill_extractor import BillExtractor
from fraud_detector import FraudDetector
from table_parser import TableParser


def load_test_data(filename: str) -> OCRInput:
    """Load test data from JSON file"""
    test_data_path = Path(__file__).parent / "test_data" / filename
    with open(test_data_path, 'r') as f:
        data = json.load(f)
    return OCRInput(**data)


def test_sample_bill_extraction():
    """Test extraction on sample valid bill"""
    print("\n=== Testing Sample Bill Extraction ===")
    
    ocr_input = load_test_data("sample_bill.json")
    extractor = BillExtractor()
    result = extractor.extract(ocr_input)
    
    assert result.meta.status == "SUCCESS", "Extraction should succeed"
    assert result.bill is not None, "Bill data should be present"
    assert len(result.bill.line_items) > 0, "Should extract line items"
    assert result.bill.final_total.value > 0, "Should extract final total"
    
    print(f"✓ Status: {result.meta.status}")
    print(f"✓ Line items extracted: {len(result.bill.line_items)}")
    print(f"✓ Final total: {result.bill.final_total.value}")
    print(f"✓ Reconciliation: {result.bill.aggregates.reconciliation_status}")
    print(f"✓ Model confidence: {result.meta.model_confidence:.2f}")
    
    # Print line items
    for item in result.bill.line_items:
        print(f"  - {item.description}: {item.quantity} × {item.unit_price} = {item.amount}")
    
    return result


def test_fraud_detection():
    """Test fraud detection on bill with arithmetic errors"""
    print("\n=== Testing Fraud Detection ===")
    
    ocr_input = load_test_data("fraud_bill.json")
    extractor = BillExtractor()
    result = extractor.extract(ocr_input)
    
    assert result.meta.status == "SUCCESS", "Extraction should succeed"
    assert len(result.bill.fraud_signals) > 0, "Should detect fraud signals"
    
    print(f"✓ Fraud signals detected: {len(result.bill.fraud_signals)}")
    
    for signal in result.bill.fraud_signals:
        print(f"  - [{signal.type}] {signal.message} (Page {signal.page})")
    
    return result


def test_table_parser():
    """Test table parsing functionality"""
    print("\n=== Testing Table Parser ===")
    
    ocr_input = load_test_data("sample_bill.json")
    parser = TableParser(ocr_input.tokens)
    rows = parser.parse()
    
    assert len(rows) > 0, "Should parse rows"
    assert parser.column_mapping, "Should map columns"
    
    print(f"✓ Rows parsed: {len(rows)}")
    print(f"✓ Column mapping: {parser.column_mapping}")
    print(f"✓ Header row index: {parser.header_row_idx}")
    
    return parser


def test_confidence_scoring():
    """Test confidence scoring"""
    print("\n=== Testing Confidence Scoring ===")
    
    ocr_input = load_test_data("sample_bill.json")
    extractor = BillExtractor()
    result = extractor.extract(ocr_input)
    
    assert result.meta.model_confidence is not None, "Should calculate confidence"
    assert 0 <= result.meta.model_confidence <= 1, "Confidence should be in [0, 1]"
    
    print(f"✓ Overall confidence: {result.meta.model_confidence:.2f}")
    
    for item in result.bill.line_items:
        print(f"  - {item.description}: confidence {item.confidence:.2f}")
    
    return result


def test_empty_input():
    """Test handling of empty input"""
    print("\n=== Testing Empty Input ===")
    
    ocr_input = OCRInput(tokens=[])
    extractor = BillExtractor()
    result = extractor.extract(ocr_input)
    
    assert result.meta.status == "FAILED", "Should fail on empty input"
    print(f"✓ Status: {result.meta.status}")
    print(f"✓ Reason: {result.meta.reason}")
    
    return result


def test_json_output():
    """Test JSON serialization"""
    print("\n=== Testing JSON Output ===")
    
    ocr_input = load_test_data("sample_bill.json")
    extractor = BillExtractor()
    result = extractor.extract(ocr_input)
    
    # Convert to JSON
    json_output = result.model_dump_json(indent=2)
    
    # Parse back
    parsed = json.loads(json_output)
    
    assert parsed['meta']['status'] == 'SUCCESS', "JSON should be valid"
    assert 'bill' in parsed, "Should contain bill data"
    
    print(f"✓ JSON output valid")
    print(f"✓ Output size: {len(json_output)} bytes")
    
    # Save to file
    output_path = Path(__file__).parent / "test_data" / "sample_output.json"
    with open(output_path, 'w') as f:
        f.write(json_output)
    
    print(f"✓ Saved to: {output_path}")
    
    return json_output


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("BILL EXTRACTION & VALIDATION AGENT - TEST SUITE")
    print("=" * 60)
    
    try:
        test_sample_bill_extraction()
        test_fraud_detection()
        test_table_parser()
        test_confidence_scoring()
        test_empty_input()
        test_json_output()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        raise
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        raise


if __name__ == "__main__":
    run_all_tests()
