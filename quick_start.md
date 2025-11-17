# 🚀 QuickStart Guide - Get Running in 10 Minutes

This guide gets you from zero to creating your first QuickBooks estimate in under 10 minutes.

---

## ⚡ Fast Track Setup

### Step 1: Install (30 seconds)

```bash
pip install -r requirements.txt
```

### Step 2: Configure (2 minutes)

```bash
# Copy template
cp .env.example .env

# Edit .env and add these 2 values (get from Intuit Developer Portal):
# QBO_CLIENT_ID=your_client_id
# QBO_CLIENT_SECRET=your_client_secret
```

**Get credentials:** https://developer.intuit.com → Create App → Keys & OAuth

### Step 3: Authorize (3 minutes)

```bash
python initial_oauth_setup.py
```

This will:
1. Open your browser
2. Ask you to sign in to QuickBooks
3. Generate tokens

Copy the `QBO_REFRESH_TOKEN` and `QBO_REALM_ID` it displays into your `.env` file.

### Step 4: Test (1 minute)

```bash
python run_tests.py
```

All tests should pass! ✅

### Step 5: Create Your First Estimate (10 seconds)

```bash
# Mock mode (no API call)
python cli_push_estimate.py --json quote_sample.json --mock

# Real mode (creates actual QuickBooks estimate)
python cli_push_estimate.py --json quote_sample.json
```

**Done!** Check the `Quotes/` folder for your PDF.

---

## 🎯 Your First Real Quote

### Create a Custom Quote JSON

```json
{
  "customer": {
    "display_name": "YOUR CUSTOMER NAME",
    "email": "customer@example.com",
    "phone": "555-0100"
  },
  "quote": {
    "reference": "GT-CUSTOM-001",
    "date": "2025-11-17"
  },
  "items": [
    {
      "description": "Interior painting - Living room",
      "qty": 1,
      "unit_price": 500.0
    },
    {
      "description": "Exterior trim - Front facade",
      "qty": 1,
      "unit_price": 300.0
    }
  ],
  "sustainability": {
    "trees": 2,
    "co2_tons": 0.2,
    "water_liters": 20
  },
  "currency": "CAD"
}
```

Save as `my_quote.json`

### Push to QuickBooks

```bash
python cli_push_estimate.py --json my_quote.json
```

**Output:**
- ✅ Estimate created in QuickBooks
- ✅ PDF downloaded to `Quotes/`
- ✅ Transaction logged to `logs/quotes_log.csv`
- ✅ JSON result printed for Excel/VBA parsing

---

## 📱 Excel VBA Integration (30 seconds)

### Add to Your Excel VBA Module

```vba
Sub CreateQuickBooksEstimate()
    Dim result As String
    
    ' Build command
    Dim cmd As String
    cmd = "python C:\GreenTech\cli_push_estimate.py --json C:\GreenTech\output\quote.json"
    
    ' Execute and capture output
    result = CreateObject("WScript.Shell").Exec(cmd).StdOut.ReadAll
    
    ' Parse JSON result (result contains the JSON output)
    Debug.Print result
End Sub
```

---

## 🔍 Troubleshooting

### "Token refresh failed"
→ Run `python initial_oauth_setup.py` again

### "Customer already exists"
→ This is normal! System finds existing customers automatically

### "PDF not found"
→ Check `Quotes/` directory exists with write permissions

### "Connection error"
→ Check internet connection and QuickBooks API status

---

## 📚 Next Steps

1. **Read full docs:** See `SETUP_GUIDE.md` for detailed setup
2. **Integrate with Kiara's engine:** Connect calculation → API
3. **Set up BigQuery:** Connect to Bruno's analytics pipeline
4. **Configure production:** Move from sandbox to production mode

---

## ✅ Success Checklist

- [ ] Dependencies installed
- [ ] `.env` configured with credentials
- [ ] OAuth flow completed
- [ ] Tests passing
- [ ] Mock estimate created
- [ ] Real estimate created in QuickBooks
- [ ] PDF downloaded successfully
- [ ] Ready to integrate with Excel!

**Total time:** ~10 minutes ⏱️

---

## 🎉 You're Live!

Your QuickBooks integration is now operational. Every quote you process will:

1. ✅ Create/find customer in QuickBooks
2. ✅ Generate professional estimate
3. ✅ Download branded PDF
4. ✅ Log transaction for analytics
5. ✅ Return structured result to Excel

**Time per quote:** <10 seconds  
**Manual work required:** Zero

---

Need help? See `SETUP_GUIDE.md` for comprehensive documentation.
