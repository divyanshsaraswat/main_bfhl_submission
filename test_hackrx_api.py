"""
Test script for HackRx Bill Extraction API
Downloads training samples and tests the extraction
"""

import requests
import json
import time
from pathlib import Path
from typing import Dict, Any

# API endpoint
API_BASE_URL = "http://localhost:8000"

# Sample document URLs from the hackathon
SAMPLE_DOCUMENTS = [
    "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_2.png?sv=2025-07-05&spr=https&st=2025-11-24T14%3A13%3A22Z&se=2026-11-25T14%3A13%3A00Z&sr=b&sp=r&sig=WFJYfNw0PJdZOpOYlsoAW0XujYGG1x2HSbcDREiFXSU%3D"
]


def test_health_check():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200


def test_extract_bill_data(document_url: str) -> Dict[str, Any]:
    """Test /extract endpoint"""
    print(f"\n=== Testing Bill Extraction ===")
    print(f"Document: {document_url[:80]}...")
    
    payload = {"document": document_url}
    
    start_time = time.time()
    response = requests.post(
        f"{API_BASE_URL}/extract",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    elapsed_time = time.time() - start_time
    
    print(f"Status Code: {response.status_code}")
    print(f"Processing Time: {elapsed_time:.2f}s")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Success: {result.get('is_success')}")
        
        # Token usage
        token_usage = result.get('token_usage', {})
        print(f"✓ Token Usage:")
        print(f"  - Total: {token_usage.get('total_tokens', 0)}")
        print(f"  - Input: {token_usage.get('input_tokens', 0)}")
        print(f"  - Output: {token_usage.get('output_tokens', 0)}")
        
        # Data
        data = result.get('data', {})
        print(f"\n✓ Extracted Data:")
        print(f"  - Total Items: {data.get('total_item_count', 0)}")
        print(f"  - Pages: {len(data.get('pagewise_line_items', []))}")
        
        # Page details
        for page_item in data.get('pagewise_line_items', []):
            print(f"\n  Page {page_item['page_no']} ({page_item['page_type']}):")
            print(f"    Items: {len(page_item['bill_items'])}")
            
            # Show first few items
            for idx, item in enumerate(page_item['bill_items'][:3], 1):
                print(f"    {idx}. {item['item_name']}")
                print(f"       Qty: {item['item_quantity']} × Rate: {item['item_rate']} = Amount: {item['item_amount']}")
            
            if len(page_item['bill_items']) > 3:
                print(f"    ... and {len(page_item['bill_items']) - 3} more items")
        
        # Calculate total
        total_amount = sum(
            item['item_amount']
            for page in data.get('pagewise_line_items', [])
            for item in page['bill_items']
        )
        print(f"\n✓ Calculated Total: ₹{total_amount:.2f}")
        
        return result
    else:
        print(f"✗ Error: {response.text}")
        return {}


def validate_response_schema(response: Dict[str, Any]) -> bool:
    """Validate response matches HackRx schema"""
    print("\n=== Validating Response Schema ===")
    
    required_fields = ['is_success', 'token_usage', 'data']
    for field in required_fields:
        if field not in response:
            print(f"✗ Missing field: {field}")
            return False
    
    # Validate token_usage
    token_fields = ['total_tokens', 'input_tokens', 'output_tokens']
    for field in token_fields:
        if field not in response['token_usage']:
            print(f"✗ Missing token_usage field: {field}")
            return False
    
    # Validate data
    data_fields = ['pagewise_line_items', 'total_item_count']
    for field in data_fields:
        if field not in response['data']:
            print(f"✗ Missing data field: {field}")
            return False
    
    # Validate pagewise items
    for page_item in response['data']['pagewise_line_items']:
        page_fields = ['page_no', 'page_type', 'bill_items']
        for field in page_fields:
            if field not in page_item:
                print(f"✗ Missing page field: {field}")
                return False
        
        # Validate page_type
        if page_item['page_type'] not in ['Bill Detail', 'Final Bill', 'Pharmacy']:
            print(f"✗ Invalid page_type: {page_item['page_type']}")
            return False
        
        # Validate bill items
        for bill_item in page_item['bill_items']:
            item_fields = ['item_name', 'item_amount', 'item_rate', 'item_quantity']
            for field in item_fields:
                if field not in bill_item:
                    print(f"✗ Missing bill_item field: {field}")
                    return False
    
    print("✓ Response schema is valid")
    return True


def save_response(response: Dict[str, Any], filename: str):
    """Save response to file"""
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / filename
    with open(output_file, 'w') as f:
        json.dump(response, f, indent=2)
    
    print(f"\n✓ Response saved to: {output_file}")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("HACKRX BILL EXTRACTION API - TEST SUITE")
    print("=" * 60)
    
    # Test health check
    if not test_health_check():
        print("\n✗ Health check failed. Is the server running?")
        print("Start the server with: python run.py")
        return
    
    # Test extraction with sample documents
    for idx, doc_url in enumerate(SAMPLE_DOCUMENTS, 1):
        response = test_extract_bill_data(doc_url)
        
        if response:
            # Validate schema
            validate_response_schema(response)
            
            # Save response
            save_response(response, f"sample_{idx}_response.json")
    
    print("\n" + "=" * 60)
    print("✓ TEST SUITE COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
