#!/usr/bin/env python3
"""
GreenTech Painting - Data Mapping Module
Transforms calculation JSON to QuickBooks API format.
"""
from typing import Dict, List, Tuple
from datetime import datetime

def validate_quote_data(data: Dict) -> Tuple[bool, str]:
    """
    Validates quote data structure.
    
    Args:
        data: Quote data dict from calculation engine
        
    Returns:
        (is_valid, error_message) tuple
    """
    # Check required top-level keys
    if "customer" not in data:
        return False, "Missing 'customer' section"
    
    if "items" not in data or not isinstance(data["items"], list):
        return False, "Missing or invalid 'items' array"
    
    if len(data["items"]) == 0:
        return False, "No items in quote"
    
    # Validate customer data
    customer = data["customer"]
    if not customer.get("display_name"):
        return False, "Customer display_name is required"
    
    # Validate items
    for i, item in enumerate(data["items"]):
        if "description" not in item:
            return False, f"Item {i}: Missing description"
        if "qty" not in item:
            return False, f"Item {i}: Missing qty"
        if "unit_price" not in item:
            return False, f"Item {i}: Missing unit_price"
        
        try:
            float(item["qty"])
            float(item["unit_price"])
        except (ValueError, TypeError):
            return False, f"Item {i}: qty and unit_price must be numeric"
    
    return True, ""

def extract_reference(data: Dict) -> str:
    """Extracts quote reference number"""
    quote = data.get("quote", {})
    return quote.get("reference", "NO-REF")

def extract_customer_name(data: Dict) -> str:
    """Extracts customer display name"""
    customer = data.get("customer", {})
    return customer.get("display_name", "Unknown Customer")

def calculate_subtotal(items: List[Dict]) -> float:
    """Calculates subtotal from items"""
    total = 0.0
    for item in items:
        qty = float(item.get("qty", 0))
        price = float(item.get("unit_price", 0))
        total += qty * price
    return total

def format_sustainability_memo(sustainability: Dict) -> str:
    """
    Formats sustainability data into a customer memo.
    
    Args:
        sustainability: Dict with trees, co2_tons, water_liters
        
    Returns:
        Formatted memo string
    """
    if not sustainability:
        return ""
    
    parts = []
    
    trees = sustainability.get("trees", 0)
    if trees:
        parts.append(f"{trees} tree(s)")
    
    co2 = sustainability.get("co2_tons", 0)
    if co2:
        parts.append(f"{co2} tons CO₂")
    
    water = sustainability.get("water_liters", 0)
    if water:
        parts.append(f"{water}L water saved")
    
    if parts:
        return "Environmental impact: " + ", ".join(parts)
    
    return ""

def map_quote_to_qbo_estimate(data: Dict, customer_id: str) -> Dict:
    """
    Maps GreenTech quote JSON to QuickBooks Estimate format.
    
    Args:
        data: Quote data from calculation engine
        customer_id: QuickBooks customer ID
        
    Returns:
        QuickBooks Estimate payload dict
    """
    items = data.get("items", [])
    quote_info = data.get("quote", {})
    sustainability = data.get("sustainability", {})
    currency = data.get("currency", "CAD")
    reference = extract_reference(data)
    
    # Build line items
    line_items = []
    for idx, item in enumerate(items, start=1):
        description = item.get("description", "Service")
        qty = float(item.get("qty", 1))
        unit_price = float(item.get("unit_price", 0))
        amount = qty * unit_price
        
        line_item = {
            "LineNum": idx,
            "Description": description,
            "DetailType": "SalesItemLineDetail",
            "Amount": amount,
            "SalesItemLineDetail": {
                "Qty": qty,
                "UnitPrice": unit_price,
                # Use a generic service item or create items dynamically
                "ItemRef": {
                    "name": description  # QBO will match by name or create
                }
            }
        }
        line_items.append(line_item)
    
    # Build estimate payload
    estimate = {
        "CustomerRef": {
            "value": customer_id
        },
        "Line": line_items,
        "CurrencyRef": {
            "value": currency
        }
    }
    
    # Add optional fields
    if reference:
        estimate["DocNumber"] = reference
    
    # Add transaction date if provided
    txn_date = quote_info.get("date")
    if txn_date:
        estimate["TxnDate"] = txn_date
    
    # Add customer memo with reference and sustainability
    memo_parts = []
    if reference:
        memo_parts.append(f"Reference: {reference}")
    
    sustainability_text = format_sustainability_memo(sustainability)
    if sustainability_text:
        memo_parts.append(sustainability_text)
    
    if memo_parts:
        estimate["CustomerMemo"] = {
            "value": " | ".join(memo_parts)
        }
    
    # Add private note for internal tracking
    if sustainability:
        estimate["PrivateNote"] = (
            f"GreenTech Quote {reference}\n"
            f"Generated: {datetime.utcnow().isoformat()}\n"
            f"Sustainability metrics included in customer memo"
        )
    
    return estimate

def extract_estimate_summary(qbo_estimate: Dict) -> Dict:
    """
    Extracts key info from QuickBooks Estimate response.
    
    Args:
        qbo_estimate: Estimate response from QBO API
        
    Returns:
        Summary dict
    """
    return {
        "id": qbo_estimate.get("Id"),
        "doc_number": qbo_estimate.get("DocNumber"),
        "total": qbo_estimate.get("TotalAmt", 0),
        "customer_id": qbo_estimate.get("CustomerRef", {}).get("value"),
        "customer_name": qbo_estimate.get("CustomerRef", {}).get("name"),
        "currency": qbo_estimate.get("CurrencyRef", {}).get("value", "CAD"),
        "txn_date": qbo_estimate.get("TxnDate"),
        "status": qbo_estimate.get("TxnStatus", "Pending")
    }

# ==================== Test/Debug ====================

if __name__ == "__main__":
    import json
    
    # Sample test data
    test_quote = {
        "customer": {
            "display_name": "Alex Smith",
            "email": "alex@example.com",
            "phone": "416-555-0100"
        },
        "quote": {
            "reference": "GT-TEST-001",
            "date": "2025-11-17"
        },
        "items": [
            {
                "description": "Interior painting - Living room",
                "qty": 2,
                "unit_price": 150.0
            },
            {
                "description": "Exterior trim - Front facade",
                "qty": 1,
                "unit_price": 300.0
            }
        ],
        "sustainability": {
            "trees": 1,
            "co2_tons": 0.15,
            "water_liters": 25
        },
        "currency": "CAD"
    }
    
    print("Testing data mapping...")
    print()
    
    # Test validation
    is_valid, error = validate_quote_data(test_quote)
    print(f"Validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
    if not is_valid:
        print(f"  Error: {error}")
    print()
    
    # Test extraction
    reference = extract_reference(test_quote)
    customer = extract_customer_name(test_quote)
    subtotal = calculate_subtotal(test_quote["items"])
    
    print(f"Reference: {reference}")
    print(f"Customer: {customer}")
    print(f"Subtotal: ${subtotal:,.2f}")
    print()
    
    # Test mapping
    mock_customer_id = "123"
    estimate_payload = map_quote_to_qbo_estimate(test_quote, mock_customer_id)
    
    print("Mapped Estimate Payload:")
    print(json.dumps(estimate_payload, indent=2))
