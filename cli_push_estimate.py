import argparse, json, pathlib, sys

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    args = ap.parse_args()

    path = pathlib.Path(args.json)
    print("✅ CLI started")
    print(f"→ JSON path: {path.resolve()}")

    # Load and show a tiny summary
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    print(f"→ Loaded {len(items)} item(s) for customer: {data.get('customer',{}).get('display_name','(unknown)')}")

    # Final status JSON (what Excel would read)
    result = {"ok": True, "received_json": str(path), "items": len(items)}
    print(json.dumps(result, indent=2))
