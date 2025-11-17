#!/usr/bin/env python3
"""
GreenTech Painting - QuickBooks Estimate Push CLI
Reads calculation JSON, creates QBO estimate, downloads PDF, logs results.
"""
import argparse
import json
import pathlib
import sys
import csv
import datetime
from typing import Dict

# Import our modules
from mapping import (
    validate_quote_data, 
    extract_reference, 
    extract_customer_name,
    calculate_subtotal,
    map_quote_to_qbo_estimate
)
from quickbooks_client import (
    get_or_create_customer,
    create_estimate,
    get_estimate_pdf,
    QuickBooksAPIError,
    get_company_info
)

# ---------- Logging Helpers ----------
def utc_now():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _ensure_trailing_newline(path: pathlib.Path):
    if path.exists() and path.stat().st_size > 0:
        with path.open("rb+") as fb:
            fb.seek(-1, 2)
            last = fb.read(1)
            if last not in (b"\n", b"\r"):
                fb.write(b"\n")

def append_log(reference, customer, items_count, subtotal, currency, status, pdf_path, error="", qbo_id=""):
    """Appends a row to the CSV log file"""
    log_path = pathlib.Path("logs/quotes_log.csv")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    new_file = not log_path.exists() or log_path.stat().st_size == 0
    if not new_file:
        _ensure_trailing_newline(log_path)

    with log_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        if new_file:
            w.writerow([
                "timestamp", "reference", "customer_name", "items_count",
                "subtotal", "currency", "status", "pdf_path", "qbo_estimate_id", "error"
            ])
        w.writerow([
            utc_now(), reference, customer, items_count,
            f"{subtotal:.2f}", currency, status, pdf_path, qbo_id, error[:200]
        ])

# ---------- Main Processing ----------
def process_quote(json_path: pathlib.Path, use_mock: bool = False) -> Dict:
    """
    Main function to process a quote JSON and push to QuickBooks.
    
    Args:
        json_path: Path to calculation JSON file
        use_mock: If True, creates mock PDF instead of calling QBO API
        
    Returns:
        Result dict with status info
    """
    print(f"{'='*60}")
    print(f"GreenTech Painting - QuickBooks Estimate Generator")
    print(f"{'='*60}")
    print(f"📄 JSON: {json_path.resolve()}")
    print(f"🔧 Mode: {'MOCK' if use_mock else 'QUICKBOOKS API'}")
    print()
    
    # 1) Load JSON
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        error_msg = f"Failed to load JSON: {e}"
        print(f"❌ {error_msg}")
        return {"ok": False, "error": error_msg}
    
    # 2) Validate data
    is_valid, validation_error = validate_quote_data(data)
    if not is_valid:
        error_msg = f"Invalid quote data: {validation_error}"
        print(f"❌ {error_msg}")
        return {"ok": False, "error": error_msg}
    
    # 3) Extract key info
    reference = extract_reference(data)
    customer_name = extract_customer_name(data)
    items = data.get("items", [])
    currency = data.get("currency", "CAD")
    subtotal = calculate_subtotal(items)
    
    print(f"📋 Reference: {reference}")
    print(f"👤 Customer: {customer_name}")
    print(f"📦 Items: {len(items)}")
    print(f"💰 Subtotal: {currency} ${subtotal:,.2f}")
    print()
    
    # 4) Process based on mode
    if use_mock:
        return process_mock(reference, customer_name, items, subtotal, currency)
    else:
        return process_quickbooks(data, reference, customer_name, items, subtotal, currency)

def process_mock(reference, customer_name, items, subtotal, currency) -> Dict:
    """Creates mock PDF for testing without QBO API"""
    print("🔨 Creating MOCK estimate...")
    
    quotes_dir = pathlib.Path("Quotes")
    quotes_dir.mkdir(parents=True, exist_ok=True)
    
    fname = f"Estimate_{reference or 'NO-REF'}.pdf"
    pdf_path = quotes_dir / fname
    
    # Generate mock PDF content
    lines = [
        "GreenTech Painting – Estimate (MOCK)\n",
        f"Reference: {reference}\n",
        f"Customer: {customer_name}\n",
        "-" * 40 + "\n",
    ]
    for item in items:
        desc = item.get("description", "Item")
        qty = item.get("qty", 1)
        price = float(item.get("unit_price", 0))
        lines.append(f"{desc}  x{qty}   ${price:.2f}\n")
    lines += ["-" * 40 + "\n", f"Subtotal: {currency} ${subtotal:.2f}\n"]
    
    pdf_path.write_text("".join(lines), encoding="utf-8")
    
    # Log result
    append_log(reference, customer_name, len(items), subtotal, currency, 
               "mock_created", str(pdf_path))
    
    result = {
        "ok": True,
        "mode": "mock",
        "reference": reference,
        "customer_name": customer_name,
        "items": len(items),
        "subtotal": round(subtotal, 2),
        "currency": currency,
        "pdf_path": str(pdf_path),
        "status": "mock_created"
    }
    
    print(f"✅ Mock PDF created: {pdf_path}")
    return result

def process_quickbooks(data, reference, customer_name, items, subtotal, currency) -> Dict:
    """Creates real QuickBooks estimate via API"""
    print("🚀 Connecting to QuickBooks Online...")
    
    try:
        # Test connection first
        company = get_company_info()
        print(f"✅ Connected to: {company.get('CompanyName', 'Unknown')}")
        print()
        
        # Step 1: Get or create customer
        print(f"👤 Getting/creating customer: {customer_name}...")
        customer_data = data.get("customer", {})
        qbo_customer = get_or_create_customer(
            display_name=customer_name,
            email=customer_data.get("email", ""),
            phone=customer_data.get("phone", "")
        )
        customer_id = qbo_customer["Id"]
        print(f"✅ Customer ID: {customer_id}")
        print()
        
        # Step 2: Create estimate
        print(f"📝 Creating estimate...")
        estimate_payload = map_quote_to_qbo_estimate(data, customer_id)
        qbo_estimate = create_estimate(estimate_payload)
        
        estimate_id = qbo_estimate["Id"]
        doc_number = qbo_estimate.get("DocNumber", reference)
        total_amt = qbo_estimate.get("TotalAmt", subtotal)
        
        print(f"✅ Estimate created!")
        print(f"   ID: {estimate_id}")
        print(f"   Doc Number: {doc_number}")
        print(f"   Total: {currency} ${total_amt:,.2f}")
        print()
        
        # Step 3: Download PDF
        print(f"📥 Downloading PDF...")
        quotes_dir = pathlib.Path("Quotes")
        quotes_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_filename = f"Estimate_{doc_number}.pdf"
        pdf_path = quotes_dir / pdf_filename
        
        get_estimate_pdf(estimate_id, str(pdf_path))
        print(f"✅ PDF saved: {pdf_path}")
        print()
        
        # Step 4: Log success
        append_log(doc_number, customer_name, len(items), total_amt, currency,
                   "created", str(pdf_path), qbo_id=estimate_id)
        
        result = {
            "ok": True,
            "mode": "quickbooks",
            "reference": doc_number,
            "customer_name": customer_name,
            "customer_id": customer_id,
            "estimate_id": estimate_id,
            "items": len(items),
            "subtotal": round(subtotal, 2),
            "total": round(total_amt, 2),
            "currency": currency,
            "pdf_path": str(pdf_path),
            "status": "created"
        }
        
        print("=" * 60)
        print("✅ SUCCESS - Estimate created in QuickBooks!")
        print("=" * 60)
        
        return result
        
    except QuickBooksAPIError as e:
        error_msg = f"QuickBooks API Error: {e.message}"
        print(f"\n❌ {error_msg}")
        print(f"   Status Code: {e.status_code}")
        
        # Log failure
        append_log(reference, customer_name, len(items), subtotal, currency,
                   "failed", "", error=error_msg)
        
        return {
            "ok": False,
            "error": error_msg,
            "status_code": e.status_code,
            "reference": reference
        }
    
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"\n❌ {error_msg}")
        
        # Log failure
        append_log(reference, customer_name, len(items), subtotal, currency,
                   "failed", "", error=error_msg)
        
        return {
            "ok": False,
            "error": error_msg,
            "reference": reference
        }

# ---------- CLI Entry Point ----------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Push GreenTech calculation to QuickBooks Estimate"
    )
    parser.add_argument("--json", required=True, help="Path to calculation JSON file")
    parser.add_argument("--mock", action="store_true", 
                       help="Create mock PDF instead of calling QuickBooks API")
    
    args = parser.parse_args()
    
    json_path = pathlib.Path(args.json)
    if not json_path.exists():
        print(f"❌ Error: JSON file not found: {json_path}")
        sys.exit(1)
    
    # Process the quote
    result = process_quote(json_path, use_mock=args.mock)
    
    # Output result as JSON (for Excel/VBA to parse)
    print()
    print("=" * 60)
    print("RESULT JSON:")
    print("=" * 60)
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if result["ok"] else 1)
