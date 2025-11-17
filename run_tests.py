#!/usr/bin/env python3
"""
GreenTech Painting - API Integration Test Suite
Runs all tests to verify the system is working correctly.
"""
import sys
import os
from pathlib import Path

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_test(test_name, passed, message=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if message:
        print(f"      {message}")

def test_environment():
    """Test 1: Environment Configuration"""
    print_header("TEST 1: Environment Configuration")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    tests = [
        ("QBO_CLIENT_ID", os.getenv("QBO_CLIENT_ID")),
        ("QBO_CLIENT_SECRET", os.getenv("QBO_CLIENT_SECRET")),
        ("QBO_REFRESH_TOKEN", os.getenv("QBO_REFRESH_TOKEN")),
        ("QBO_REALM_ID", os.getenv("QBO_REALM_ID")),
        ("QBO_MODE", os.getenv("QBO_MODE")),
    ]
    
    all_passed = True
    for var_name, value in tests:
        passed = value is not None and value != ""
        all_passed = all_passed and passed
        print_test(f"Environment variable: {var_name}", passed, 
                  f"Value: {value[:20] + '...' if value and len(value) > 20 else value or 'NOT SET'}")
    
    return all_passed

def test_oauth():
    """Test 2: OAuth Token Management"""
    print_header("TEST 2: OAuth Token Management")
    
    try:
        from oauth import get_access_token
        
        token = get_access_token()
        passed = token is not None and len(token) > 20
        print_test("Token refresh", passed, 
                  f"Token: {token[:30]}..." if passed else "Failed to get token")
        return passed
    except Exception as e:
        print_test("Token refresh", False, f"Error: {e}")
        return False

def test_quickbooks_connection():
    """Test 3: QuickBooks API Connection"""
    print_header("TEST 3: QuickBooks API Connection")
    
    try:
        from quickbooks_client import get_company_info, QuickBooksAPIError
        
        company = get_company_info()
        company_name = company.get("CompanyName", "Unknown")
        
        print_test("API connection", True, f"Connected to: {company_name}")
        print(f"      Company ID: {company.get('Id')}")
        print(f"      Address: {company.get('CompanyAddr', {}).get('City', 'N/A')}")
        return True
    except QuickBooksAPIError as e:
        print_test("API connection", False, f"API Error: {e.message}")
        return False
    except Exception as e:
        print_test("API connection", False, f"Error: {e}")
        return False

def test_mapping():
    """Test 4: Data Mapping Functions"""
    print_header("TEST 4: Data Mapping Functions")
    
    try:
        from mapping import validate_quote_data, map_quote_to_qbo_estimate
        import json
        
        # Load sample quote
        sample_path = Path("quote_sample.json")
        if not sample_path.exists():
            print_test("Sample quote file", False, "quote_sample.json not found")
            return False
        
        quote_data = json.loads(sample_path.read_text())
        
        # Test validation
        is_valid, error = validate_quote_data(quote_data)
        print_test("Quote validation", is_valid, error if not is_valid else "Valid")
        
        if not is_valid:
            return False
        
        # Test mapping
        estimate = map_quote_to_qbo_estimate(quote_data, "123")
        has_customer = "CustomerRef" in estimate
        has_lines = len(estimate.get("Line", [])) > 0
        
        print_test("Quote mapping", has_customer and has_lines,
                  f"Mapped {len(estimate.get('Line', []))} line items")
        
        return is_valid and has_customer and has_lines
    except Exception as e:
        print_test("Data mapping", False, f"Error: {e}")
        return False

def test_mock_estimate():
    """Test 5: Mock Estimate Creation"""
    print_header("TEST 5: Mock Estimate Creation")
    
    try:
        import subprocess
        
        result = subprocess.run(
            ["python", "cli_push_estimate.py", "--json", "quote_sample.json", "--mock"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        passed = result.returncode == 0
        print_test("Mock estimate creation", passed)
        
        if passed:
            # Check if PDF was created
            pdf_path = Path("Quotes")
            if pdf_path.exists():
                pdfs = list(pdf_path.glob("*.pdf"))
                print(f"      Created {len(pdfs)} PDF(s)")
        
        return passed
    except Exception as e:
        print_test("Mock estimate creation", False, f"Error: {e}")
        return False

def test_customer_operations():
    """Test 6: Customer Operations"""
    print_header("TEST 6: Customer CRUD Operations")
    
    try:
        from quickbooks_client import query_customers, QuickBooksAPIError
        
        # Query existing customers
        customers = query_customers()
        print_test("Query customers", True, f"Found {len(customers)} customer(s)")
        
        return True
    except QuickBooksAPIError as e:
        print_test("Customer operations", False, f"API Error: {e.message}")
        return False
    except Exception as e:
        print_test("Customer operations", False, f"Error: {e}")
        return False

def test_full_estimate_creation():
    """Test 7: Full Estimate Creation (OPTIONAL - creates real data)"""
    print_header("TEST 7: Full Estimate Creation (Optional)")
    
    print("⚠️  This test creates a REAL estimate in QuickBooks.")
    print("   It will consume API quota and create test data.")
    print()
    
    response = input("Do you want to run this test? (yes/no): ").strip().lower()
    
    if response != "yes":
        print("⏭️  Skipping full estimate creation test")
        return True
    
    try:
        import subprocess
        
        result = subprocess.run(
            ["python", "cli_push_estimate.py", "--json", "quote_sample.json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        passed = result.returncode == 0
        print_test("Full estimate creation", passed)
        
        if passed:
            print("\n   Output:")
            for line in result.stdout.split('\n')[-15:]:  # Last 15 lines
                if line.strip():
                    print(f"   {line}")
        else:
            print("\n   Errors:")
            print(f"   {result.stderr}")
        
        return passed
    except Exception as e:
        print_test("Full estimate creation", False, f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  GreenTech Painting - API Integration Test Suite")
    print("=" * 70)
    print()
    print("This test suite will verify that your QuickBooks API")
    print("integration is configured correctly and working.")
    print()
    
    # Check if we're in the right directory
    if not Path("cli_push_estimate.py").exists():
        print("❌ Error: Run this script from the project root directory")
        print("   (where cli_push_estimate.py is located)")
        sys.exit(1)
    
    # Run tests
    results = []
    
    results.append(("Environment", test_environment()))
    results.append(("OAuth", test_oauth()))
    results.append(("QuickBooks Connection", test_quickbooks_connection()))
    results.append(("Data Mapping", test_mapping()))
    results.append(("Mock Estimate", test_mock_estimate()))
    results.append(("Customer Operations", test_customer_operations()))
    results.append(("Full Estimate (Optional)", test_full_estimate_creation()))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Total: {passed_count}/{total_count} tests passed")
    print()
    
    if passed_count == total_count:
        print("🎉 All tests passed! Your QuickBooks integration is ready.")
        print()
        print("Next steps:")
        print("1. Integrate with Kiara's calculation engine")
        print("2. Set up VBA trigger in Excel")
        print("3. Connect to Bruno's BigQuery for analytics")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        print()
        print("Common issues:")
        print("- Missing or incorrect .env configuration")
        print("- Expired refresh token (run initial_oauth_setup.py)")
        print("- Network connectivity issues")
        print("- QuickBooks API permissions")
        sys.exit(1)

if __name__ == "__main__":
    main()
