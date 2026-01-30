#!/usr/bin/env python3
"""
Create Master JSON for Eaton Products

Consolidates all information from multiple sources:
- BMEcat product data
- Product images with Vision metadata
- Documentation mentions across all PDFs/catalogs
- Related products
- Technical specifications

Generates comprehensive product JSON for RAG/API use.
"""

import json
import sys
from pathlib import Path
import argparse

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_master_json(product_id: str, lakehouse_path: Path, output_path: Path = None):
    """Create master JSON for a product from all data sources"""

    import lancedb
    import pandas as pd
    from deltalake import DeltaTable

    print(f"Creating Master JSON for: {product_id}")
    print("="*70)

    master_data = {
        "product_id": product_id,
        "generated_at": "2026-01-11T23:20:00Z",
        "master_data": {},
        "images": [],
        "documentation": {
            "chunks": [],
            "total_mentions": 0
        },
        "technical_specs": {},
        "related_products": [],
        "data_sources": [],
        "completeness_score": 0.0
    }

    # 1. Query BMEcat Product Data
    print("\n[1/5] Querying BMEcat...")
    try:
        products_path = lakehouse_path / "delta" / "eaton_products"
        products_dt = DeltaTable(str(products_path))
        products_df = products_dt.to_pandas()
        product = products_df[products_df['supplier_pid'] == product_id]

        if len(product) > 0:
            p = product.iloc[0]
            master_data['master_data']['from_bmecat'] = {
                "supplier_pid": str(p['supplier_pid']),
                "manufacturer_pid": str(p['manufacturer_pid']),
                "manufacturer_name": str(p['manufacturer_name']),
                "product_name": str(p['product_name']),
                "short_description": str(p['short_description']),
                "long_description": str(p['long_description']),
                "etim_class": str(p['etim_class']) if p['etim_class'] else None,
                "eclass_code": str(p['eclass_code']) if p['eclass_code'] else None,
                "ean_upc": str(p['ean_upc']) if p['ean_upc'] else None,
                "manufacturer_type_descr": str(p['manufacturer_type_descr']) if p['manufacturer_type_descr'] else None,
                "specifications": json.loads(p['specifications']) if p['specifications'] else {},
                "mime_sources": json.loads(p['mime_sources']) if p['mime_sources'] else [],
                "price": float(p['price']) if p['price'] and not pd.isna(p['price']) else None,
                "currency": str(p['currency']) if p['currency'] else None,
                "country_of_origin": str(p['country_of_origin']) if p['country_of_origin'] else None
            }
            master_data['data_sources'].append('bmecat')
            print(f"  ✓ Found in BMEcat: {p['product_name']}")
    except Exception as e:
        print(f"  ✗ BMEcat error: {e}")

    # 2. Query Product Images
    print("\n[2/5] Querying product images...")
    try:
        images_path = lakehouse_path / "delta" / "product_images"
        images_dt = DeltaTable(str(images_path))
        images_df = images_dt.to_pandas()
        product_images = images_df[images_df['product_id'] == product_id]

        for _, img in product_images.iterrows():
            master_data['images'].append({
                "filename": str(img['image_filename']),
                "type": str(img['image_type']),
                "orientation": str(img['view_orientation']),
                "perspective": str(img['view_perspective']),
                "seo_description": str(img['seo_description']),
                "visible_specs": str(img['visible_specs']),
                "url": str(img['image_url']),
                "has_vision_metadata": bool(img['has_vision_metadata'])
            })

        if len(master_data['images']) > 0:
            master_data['data_sources'].append('product_images')
            print(f"  ✓ Found {len(master_data['images'])} images")
    except Exception as e:
        print(f"  ✗ Images error: {e}")

    # 3. Query All Documentation Mentions
    print("\n[3/5] Searching all embeddings...")
    try:
        lance_path = lakehouse_path / "lance"
        db = lancedb.connect(str(lance_path))
        table = db.open_table('embeddings')

        df = table.to_pandas()

        # Search for product mentions
        import pandas as pd
        mentions = df[
            df['text'].str.contains(product_id, case=False, na=False) |
            df['text'].str.contains('5E UPS|Eaton 5E', case=False, na=False)
        ]

        for _, chunk in mentions.head(20).iterrows():
            master_data['documentation']['chunks'].append({
                "source": str(chunk['filename']),
                "chunk_index": int(chunk['chunk_index']),
                "text": str(chunk['text'])[:500],  # First 500 chars
                "mcp": str(chunk['mcp'])
            })

        master_data['documentation']['total_mentions'] = len(mentions)

        if len(mentions) > 0:
            master_data['data_sources'].append('embeddings')
            print(f"  ✓ Found {len(mentions)} mentions in documents")
    except Exception as e:
        print(f"  ✗ Embeddings error: {e}")

    # 4. Find Related Products
    print("\n[4/5] Finding related products...")
    try:
        if master_data['master_data'].get('from_bmecat', {}).get('etim_class'):
            etim = master_data['master_data']['from_bmecat']['etim_class']
            related = products_df[
                (products_df['etim_class'] == etim) &
                (products_df['supplier_pid'] != product_id)
            ]

            for _, r in related.head(5).iterrows():
                master_data['related_products'].append({
                    "supplier_pid": str(r['supplier_pid']),
                    "product_name": str(r['product_name']),
                    "etim_class": str(r['etim_class'])
                })

            print(f"  ✓ Found {len(related)} related products (ETIM: {etim})")
    except Exception as e:
        print(f"  ✗ Related products error: {e}")

    # 5. Calculate Completeness Score
    print("\n[5/5] Calculating data completeness...")
    fields_total = 15
    fields_filled = 0

    if master_data['master_data'].get('from_bmecat'):
        bme = master_data['master_data']['from_bmecat']
        for key, value in bme.items():
            if value and value not in [None, '', {}, []]:
                fields_filled += 1

    master_data['completeness_score'] = round(fields_filled / fields_total, 2)
    master_data['data_quality'] = {
        "fields_filled": fields_filled,
        "fields_total": fields_total,
        "has_images": len(master_data['images']) > 0,
        "has_documentation": master_data['documentation']['total_mentions'] > 0,
        "has_specifications": bool(master_data['master_data'].get('from_bmecat', {}).get('specifications')),
        "has_etim_classification": bool(master_data['master_data'].get('from_bmecat', {}).get('etim_class'))
    }

    print(f"  ✓ Completeness: {master_data['completeness_score']*100:.0f}%")

    # Output
    print("\n" + "="*70)
    print("MASTER JSON CREATED")
    print("="*70)
    print(json.dumps(master_data, indent=2, ensure_ascii=False))

    # Save to file
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(master_data, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved to: {output_path}")

    return master_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create product master JSON")
    parser.add_argument("product_id", help="Product ID (supplier_pid)")
    parser.add_argument(
        "--lakehouse",
        default="data/lakehouse/eaton",
        help="Lakehouse path"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON file path"
    )

    args = parser.parse_args()

    lakehouse_path = Path(args.lakehouse)
    output_path = Path(args.output) if args.output else lakehouse_path / f"{args.product_id}_master.json"

    create_master_json(args.product_id, lakehouse_path, output_path)
