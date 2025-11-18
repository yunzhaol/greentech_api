#!/usr/bin/env python3
"""
GreenTech Painting - QuickBooks API Client
Handles all QuickBooks Online API interactions.
"""
import os
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv
from oauth import get_auth_header

load_dotenv()

# Configuration
REALM_ID = os.getenv("QBO_REALM_ID")
QBO_MODE = os.getenv("QBO_MODE", "sandbox")

def get_base_url():
    """Returns the QuickBooks API base URL based on mode"""
    if QBO_MODE == "production":
        return "https://quickbooks.api.intuit.com"
    return "https://sandbox-quickbooks.api.intuit.com"

class QuickBooksAPIError(Exception):
    """Custom exception for QuickBooks API errors"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)

def _make_request(method: str, endpoint: str, data: dict = None, params: dict = None) -> dict:
    """
    Makes authenticated request to QuickBooks API.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        data: JSON payload for POST/PUT
        params: Query parameters
        
    Returns:
        Response JSON
        
    Raises:
        QuickBooksAPIError on failure
    """
    if not REALM_ID:
        raise QuickBooksAPIError("QBO_REALM_ID not set in environment")
    
    url = f"{get_base_url()}/v3/company/{REALM_ID}/{endpoint}"
    
    headers = {
        **get_auth_header(),
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params,
            timeout=30
        )
        
        if response.status_code >= 400:
            error_data = response.json() if response.text else {}
            fault = error_data.get("Fault", {})
            error_msg = fault.get("Error", [{}])[0].get("Message", response.text)
            
            raise QuickBooksAPIError(
                message=error_msg,
                status_code=response.status_code,
                response_data=error_data
            )
        
        return response.json()
    
    except requests.exceptions.RequestException as e:
        raise QuickBooksAPIError(f"Network error: {str(e)}")

# ==================== Company Info ====================

def get_company_info() -> Dict:
    """
    Gets company information to verify connection.
    
    Returns:
        Company info dict with CompanyName, Id, etc.
    """
    response = _make_request("GET", "companyinfo/1")
    return response.get("CompanyInfo", {})

# ==================== Customer Operations ====================

def query_customers(display_name: str = None) -> List[Dict]:
    """
    Queries customers from QuickBooks.
    
    Args:
        display_name: Optional filter by display name
        
    Returns:
        List of customer dicts
    """
    if display_name:
        # Escape single quotes in SQL query
        escaped_name = display_name.replace("'", "\\'")
        query = f"SELECT * FROM Customer WHERE DisplayName = '{escaped_name}'"
    else:
        query = "SELECT * FROM Customer MAXRESULTS 100"
    
    response = _make_request("GET", "query", params={"query": query})
    query_response = response.get("QueryResponse", {})
    return query_response.get("Customer", [])

def get_customer_by_id(customer_id: str) -> Dict:
    """
    Gets a customer by ID.
    
    Args:
        customer_id: QuickBooks customer ID
        
    Returns:
        Customer dict
    """
    response = _make_request("GET", f"customer/{customer_id}")
    return response.get("Customer", {})

def create_customer(display_name: str, email: str = "", phone: str = "") -> Dict:
    """
    Creates a new customer in QuickBooks.
    
    Args:
        display_name: Customer name
        email: Email address (optional)
        phone: Phone number (optional)
        
    Returns:
        Created customer dict with Id
    """
    payload = {
        "DisplayName": display_name,
        "PrimaryEmailAddr": {"Address": email} if email else None,
        "PrimaryPhone": {"FreeFormNumber": phone} if phone else None
    }
    
    # Remove None values
    payload = {k: v for k, v in payload.items() if v is not None}
    
    response = _make_request("POST", "customer", data=payload)
    return response.get("Customer", {})

def get_or_create_customer(display_name: str, email: str = "", phone: str = "") -> Dict:
    """
    Gets existing customer or creates new one.
    
    Args:
        display_name: Customer name
        email: Email address
        phone: Phone number
        
    Returns:
        Customer dict with Id
    """
    # Try to find existing customer
    existing = query_customers(display_name=display_name)
    
    if existing:
        customer = existing[0]
        print(f"[QBO] Found existing customer: {customer['DisplayName']} (ID: {customer['Id']})")
        return customer
    
    # Create new customer
    print(f"[QBO] Creating new customer: {display_name}")
    return create_customer(display_name, email, phone)

# ==================== Estimate Operations ====================

def create_estimate(estimate_data: Dict) -> Dict:
    """
    Creates an estimate in QuickBooks.
    
    Args:
        estimate_data: Estimate payload (use mapping.py to generate)
        
    Returns:
        Created estimate dict with Id
    """
    response = _make_request("POST", "estimate", data=estimate_data)
    return response.get("Estimate", {})

def get_estimate(estimate_id: str) -> Dict:
    """
    Gets an estimate by ID.
    
    Args:
        estimate_id: QuickBooks estimate ID
        
    Returns:
        Estimate dict
    """
    response = _make_request("GET", f"estimate/{estimate_id}")
    return response.get("Estimate", {})

def get_estimate_pdf(estimate_id: str, output_path: str) -> str:
    """
    Downloads estimate PDF.
    
    Args:
        estimate_id: QuickBooks estimate ID
        output_path: Local file path to save PDF
        
    Returns:
        Path to saved PDF file
    """
    if not REALM_ID:
        raise QuickBooksAPIError("QBO_REALM_ID not set")
    
    url = f"{get_base_url()}/v3/company/{REALM_ID}/estimate/{estimate_id}/pdf"
    
    headers = {
        **get_auth_header(),
        "Accept": "application/pdf"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code >= 400:
            raise QuickBooksAPIError(
                f"Failed to download PDF: {response.status_code}",
                status_code=response.status_code
            )
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        print(f"[QBO] PDF downloaded: {output_path}")
        return output_path
    
    except requests.exceptions.RequestException as e:
        raise QuickBooksAPIError(f"Network error downloading PDF: {str(e)}")

# ==================== Item Operations ====================

def query_items(name: str = None) -> List[Dict]:
    """
    Queries items (products/services) from QuickBooks.
    
    Args:
        name: Optional filter by name
        
    Returns:
        List of item dicts
    """
    if name:
        escaped_name = name.replace("'", "\\'")
        query = f"SELECT * FROM Item WHERE Name = '{escaped_name}'"
    else:
        query = "SELECT * FROM Item WHERE Type = 'Service' MAXRESULTS 100"
    
    response = _make_request("GET", "query", params={"query": query})
    query_response = response.get("QueryResponse", {})
    return query_response.get("Item", [])

# ==================== Test/Debug ====================

if __name__ == "__main__":
    print("Testing QuickBooks API connection...")
    print(f"Mode: {QBO_MODE}")
    print(f"Realm ID: {REALM_ID}")
    print()
    
    try:
        # Test 1: Company info
        company = get_company_info()
        print(f"✅ Connected to: {company.get('CompanyName', 'Unknown')}")
        print(f"   Address: {company.get('CompanyAddr', {}).get('City', 'N/A')}")
        print()
        
        # Test 2: Query customers
        customers = query_customers()
        print(f"✅ Found {len(customers)} customer(s)")
        if customers:
            print(f"   First customer: {customers[0].get('DisplayName')}")
        print()
        
        # Test 3: Query items
        items = query_items()
        print(f"✅ Found {len(items)} service item(s)")
        if items:
            print(f"   First item: {items[0].get('Name')}")
        
    except QuickBooksAPIError as e:
        print(f"❌ API Error: {e.message}")
        if e.status_code:
            print(f"   Status Code: {e.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
