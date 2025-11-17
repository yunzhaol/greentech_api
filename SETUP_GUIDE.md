# GreenTech Painting - QuickBooks API Setup Guide

Complete setup instructions for the QuickBooks Online API integration.

---

## 📋 Prerequisites

- Python 3.8 or higher
- QuickBooks Online account (Sandbox or Production)
- Intuit Developer account

---

## 🚀 Part 1: Initial Setup

### Step 1: Install Dependencies

```bash
pip install requests python-dotenv
```

### Step 2: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your credentials (steps below)

3. **IMPORTANT:** Add `.env` to your `.gitignore`:
   ```bash
   echo ".env" >> .gitignore
   ```

---

## 🔑 Part 2: Get QuickBooks API Credentials

### Step 1: Create Intuit Developer App

1. Go to [Intuit Developer Portal](https://developer.intuit.com)
2. Sign in with your Intuit account
3. Click **"Create an app"**
4. Select **"QuickBooks Online and Payments"**
5. Name your app (e.g., "GreenTech Quoting System")
6. Select **Development** (Sandbox) for testing

### Step 2: Get Client ID and Client Secret

1. In your app dashboard, go to **"Keys & OAuth"**
2. Copy your **Client ID** and **Client Secret**
3. Add them to your `.env` file:
   ```bash
   QBO_CLIENT_ID=your_client_id_here
   QBO_CLIENT_SECRET=your_client_secret_here
   ```

### Step 3: Configure Redirect URI

1. In the **"Keys & OAuth"** section, find **"Redirect URIs"**
2. Add this URI for testing:
   ```
   https://developer.intuit.com/oauth2/http-redirect
   ```
3. Click **Save**

### Step 4: Verify Scopes

Ensure these scopes are enabled:
- ✅ `com.intuit.quickbooks.accounting`
- ✅ `openid`
- ✅ `profile`
- ✅ `email`

---

## 🔐 Part 3: Complete OAuth 2.0 Authorization

### Run the Initial OAuth Setup

```bash
python initial_oauth_setup.py
```

This script will:
1. Open your browser to QuickBooks authorization page
2. Ask you to sign in and select a company
3. Redirect you to a URL with `code` and `realmId` parameters
4. Exchange the code for access and refresh tokens

### Extract Values from Redirect URL

After authorizing, you'll see a URL like:
```
https://developer.intuit.com/oauth2/http-redirect?
  code=L3114709614564VSU8JSEiPkXx1xhV8D9mv4xbv6sZJycibMUI&
  realmId=1231434565226279&
  state=security_token_greentech_12345
```

Copy these values:
- **code**: The long authorization code
- **realmId**: Your QuickBooks company ID

### Update Your .env File

Add these to your `.env`:
```bash
QBO_REFRESH_TOKEN=<token from script output>
QBO_REALM_ID=<realmId from URL>
QBO_MODE=sandbox
```

---

## ✅ Part 4: Test Your Connection

### Test 1: Verify Environment Setup

```bash
python test_env.py
```

Expected output:
```
Mode: sandbox
Logs path: logs/quotes_log.csv
```

### Test 2: Test OAuth Token Refresh

```bash
python oauth.py
```

Expected output:
```
[OAuth] Refreshing access token...
[OAuth] ✅ Token refreshed successfully
[OAuth] Access token expires in 3600 seconds
✅ Access token obtained: eJlbmMiOiJBMTI4Q0JDL...
```

### Test 3: Test QuickBooks API Connection

```bash
python quickbooks_client.py
```

Expected output:
```
Testing QuickBooks API connection (sandbox mode)...
Realm ID: 1231434565226279
✅ Connected to: GreenTech Painting Sandbox
   Address: Toronto
✅ Found 3 customer(s)
```

### Test 4: Create Mock Estimate

```bash
python cli_push_estimate.py --json quote_sample.json --mock
```

This creates a mock PDF without calling QuickBooks.

### Test 5: Create Real QuickBooks Estimate

```bash
python cli_push_estimate.py --json quote_sample.json
```

This creates an actual estimate in QuickBooks and downloads the PDF!

---

## 📁 Project File Structure

```
GreenTech_API/
├── .env                          # Your credentials (DO NOT COMMIT)
├── .env.example                  # Template for .env
├── .gitignore                    # Excludes .env and sensitive files
├── initial_oauth_setup.py        # One-time OAuth setup script
├── oauth.py                      # Token management
├── quickbooks_client.py          # QuickBooks API client
├── mapping.py                    # JSON → QBO payload mapping
├── cli_push_estimate.py          # Main CLI script
├── test_env.py                   # Environment test
├── quote_sample.json             # Sample quote for testing
├── logs/
│   └── quotes_log.csv           # CSV log of all quotes
└── Quotes/
    └── Estimate_*.pdf           # Downloaded estimate PDFs
```

---

## 🔄 Part 5: Token Maintenance

### Access Tokens
- **Expire:** 1 hour (3600 seconds)
- **Handled:** Automatically refreshed by `oauth.py`

### Refresh Tokens
- **Expire:** 100 days (rolling)
- **Action needed:** Reauthorize when expired

### Monitor Token Expiration

The system automatically tracks token expiration. If you see this error:
```
❌ Token refresh failed: 400 - invalid_grant
```

**Solution:** Run `initial_oauth_setup.py` again to get a new refresh token.

---

## 🛠️ Part 6: Integration with Excel/VBA

### VBA Trigger Example

```vba
Sub CreateEstimate()
    Dim pythonPath As String
    Dim scriptPath As String
    Dim jsonPath As String
    Dim command As String
    
    ' Set paths
    pythonPath = "C:\Python39\python.exe"
    scriptPath = "C:\GreenTech_API\cli_push_estimate.py"
    jsonPath = "C:\GreenTech_API\output\quote_latest.json"
    
    ' Build command
    command = pythonPath & " " & scriptPath & " --json " & jsonPath
    
    ' Execute
    Dim shell As Object
    Set shell = CreateObject("WScript.Shell")
    shell.Run command, 1, True  ' 1 = show window, True = wait for completion
End Sub
```

### Parse JSON Response

The script outputs a JSON result you can parse:
```json
{
  "ok": true,
  "mode": "quickbooks",
  "reference": "GT-TEST-001",
  "customer_name": "Alex Smith",
  "estimate_id": "145",
  "pdf_path": "Quotes/Estimate_GT-TEST-001.pdf",
  "status": "created"
}
```

---

## 🚨 Troubleshooting

### Error: "QBO_CLIENT_ID and QBO_CLIENT_SECRET must be set"
**Solution:** Check your `.env` file has these values set.

### Error: "Token refresh failed: 400"
**Solution:** Your refresh token expired. Run `initial_oauth_setup.py` again.

### Error: "QBO API Error 401: Unauthorized"
**Solution:** Access token invalid. Try `python oauth.py` to test token refresh.

### Error: "Customer already exists"
**Solution:** This is normal! The system finds existing customers automatically.

### PDF not downloading
**Solution:** Check that `Quotes/` directory exists and has write permissions.

---

## 📊 Part 7: BigQuery Integration (Optional)

To log quotes to BigQuery for analytics:

1. Install BigQuery client:
   ```bash
   pip install google-cloud-bigquery
   ```

2. Create a service account and download credentials JSON

3. Add to your Python code:
   ```python
   from google.cloud import bigquery
   
   def log_to_bigquery(quote_data):
       client = bigquery.Client()
       table_id = "your-project.dataset.quotes"
       
       rows_to_insert = [{
           "timestamp": utc_now(),
           "reference": quote_data["reference"],
           "customer": quote_data["customer_name"],
           # ... more fields
       }]
       
       errors = client.insert_rows_json(table_id, rows_to_insert)
   ```

---

## 🔒 Security Best Practices

1. ✅ **Never commit `.env` file** to version control
2. ✅ **Use environment variables** for all credentials
3. ✅ **Deploy Python script on secure server**, not on field staff laptops
4. ✅ **VBA triggers remote service** via HTTP/API call
5. ✅ **Rotate tokens regularly** (monitor 100-day expiration)
6. ✅ **Use production credentials only in production**
7. ✅ **Test everything in sandbox first**

---

## 📞 Support Resources

- [QuickBooks API Documentation](https://developer.intuit.com/app/developer/qbo/docs/get-started)
- [OAuth 2.0 Guide](https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/oauth-2.0)
- [API Explorer](https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/estimate)

---

## ✅ Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install requests python-dotenv`)
- [ ] Intuit Developer app created
- [ ] `.env` file configured with CLIENT_ID and CLIENT_SECRET
- [ ] OAuth flow completed (`python initial_oauth_setup.py`)
- [ ] REFRESH_TOKEN and REALM_ID added to `.env`
- [ ] Connection tested (`python quickbooks_client.py`)
- [ ] Mock estimate tested (`--mock` flag)
- [ ] Real estimate created successfully

---

## 🎉 You're Ready!

Your QuickBooks API integration is now complete. The system will:
- ✅ Automatically refresh access tokens
- ✅ Create/find customers in QuickBooks
- ✅ Generate estimates with line items
- ✅ Download PDF estimates
- ✅ Log all transactions to CSV
- ✅ Return structured JSON results

**Next steps:** Integrate with Kiara's calculation engine and Bruno's BigQuery setup!
