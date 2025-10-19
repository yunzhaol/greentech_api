import argparse, json, pathlib, sys, csv, datetime

# ---------- helpers ----------
import pathlib, csv, datetime

def utc_now():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _ensure_trailing_newline(path: pathlib.Path):
    if path.exists() and path.stat().st_size > 0:
        with path.open("rb+") as fb:
            fb.seek(-1, 2)
            last = fb.read(1)
            if last not in (b"\n", b"\r"):
                fb.write(b"\n")

def append_log(reference, customer, items_count, subtotal, currency, status, pdf_path, error=""):
    log_path = pathlib.Path("logs/quotes_log.csv")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # If file exists but doesn’t end with newline, add one.
    new_file = not log_path.exists() or log_path.stat().st_size == 0
    if not new_file:
        _ensure_trailing_newline(log_path)

    with log_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")  # normalize terminator
        if new_file:
            w.writerow([
                "timestamp","reference","customer_name","items_count",
                "subtotal","currency","status","pdf_path","error"
            ])
        w.writerow([
            utc_now(), reference, customer, items_count,
            f"{subtotal:.2f}", currency, status, pdf_path, error[:200]
        ])


def save_mock_pdf(reference, customer_name, items, subtotal, currency):
    # simple placeholder file so you can see an output; swap later for real QBO PDF
    quotes_dir = pathlib.Path("Quotes")
    quotes_dir.mkdir(parents=True, exist_ok=True)
    fname = f"Estimate_{reference or 'NO-REF'}.pdf"
    out = quotes_dir / fname
    lines = [
        "GreenTech Painting — Estimate (MOCK)\n",
        f"Reference: {reference}\n",
        f"Customer: {customer_name}\n",
        "-"*40 + "\n",
    ]
    for i in items:
        desc = i.get("description","Item")
        qty = i.get("qty",1)
        price = float(i.get("unit_price",0))
        lines.append(f"{desc}  x{qty}   ${price:.2f}\n")
    lines += ["-"*40 + "\n", f"Subtotal: {currency} {subtotal:.2f}\n"]
    out.write_text("".join(lines), encoding="utf-8")
    return str(out)

# ---------- main ----------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    args = ap.parse_args()

    path = pathlib.Path(args.json)
    print("✅ CLI started")
    print(f"→ JSON path: {path.resolve()}")

    # 1) LOAD JSON  -----------------------------------------
    data = json.loads(path.read_text(encoding="utf-8"))

    # 2) EXTRACT + SUBTOTAL  --------------------------------
    customer   = data.get("customer", {}) or {}
    quote      = data.get("quote", {}) or {}
    items      = data.get("items", []) or []
    currency   = data.get("currency", "CAD")
    customer_name = customer.get("display_name", "(unknown)")
    reference     = quote.get("reference", "NO-REF")

    subtotal = sum((float(i.get("unit_price", 0)) * (i.get("qty", 1) or 1)) for i in items)

    print(f"→ Loaded {len(items)} item(s) for customer: {customer_name}")
    print(f"→ Subtotal: {currency} {subtotal:.2f}")

    # 3) MOCK "PDF" OUTPUT  ---------------------------------
    pdf_path = save_mock_pdf(reference, customer_name, items, subtotal, currency)

    # 4) LOG ROW  -------------------------------------------
    append_log(reference, customer_name, len(items), subtotal, currency, "mock_created", pdf_path)

    # 5) FINAL STATUS JSON (Excel can parse this) -----------
    result = {
        "ok": True,
        "reference": reference,
        "customer_name": customer_name,
        "items": len(items),
        "subtotal": round(subtotal, 2),
        "currency": currency,
        "pdf_path": pdf_path,
        "status": "mock_created"
    }
    print(json.dumps(result, indent=2))
