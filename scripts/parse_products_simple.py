#!/usr/bin/env python3
"""
Simple product parser - Parse tab-separated text from lakehouse
No Claude needed, just Python string parsing
"""
import asyncio
import httpx
import json

async def parse_and_save_products():
    """Parse products from text and save to lakehouse"""

    # Get raw text from lakehouse
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://localhost:8502/delta/query/products_documents?limit=1")
        data = resp.json()
        doc = data["rows"][0]
        text = doc["text"]

    print(f"✅ Got text: {len(text)} chars")

    # Parse tab-separated data
    lines = text.split("\n")
    # Find the header line
    header_line = None
    for i, line in enumerate(lines):
        if line.startswith("Code\t"):
            header_line = i
            break

    if header_line is None:
        print("❌ Header not found!")
        return

    headers = lines[header_line].split("\t")
    print(f"✅ Headers: {headers[:10]}")

    # Parse products
    products = []
    for line in lines[header_line+1:]:
        if not line.strip():
            continue
        values = line.split("\t")
        if len(values) < len(headers):
            continue

        product = {}
        for i, header in enumerate(headers):
            if i < len(values):
                product[header] = values[i]

        # Map to standard fields
        prod_record = {
            "sku": product.get("Code", ""),
            "short_description": product.get("Kurztext", ""),
            "long_description": product.get("Langtext", ""),
            "product_family": product.get("Produktfamilie", ""),
            "product_name": product.get("Produktname", ""),
            "price_eur": product.get("Preis 0 in EUR (VK0)", ""),
            "manufacturer": "Lightnet",
            "brand": "Lightnet",
            "status": product.get("Status", "active")
        }
        products.append(prod_record)

    print(f"✅ Parsed {len(products)} products")
    print(f"Sample: {products[0]}")

    # Save to lakehouse
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "http://localhost:8502/delta/insert/syndication_products",
            json={"records": products}
        )
        print(f"Save response: {resp.status_code}")
        print(f"Response: {resp.text[:500]}")

if __name__ == "__main__":
    asyncio.run(parse_and_save_products())
