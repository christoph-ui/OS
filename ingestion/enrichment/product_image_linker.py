"""
Product-Image Linker

Links product images to products using CSV mappings and Vision API metadata.

Combines:
1. CSV mappings (catalog_number → image_filename)
2. Vision API metadata (orientation, specs, SEO descriptions)
3. Product data from BMEcat

Creates enriched product_images table for multi-modal search.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict
import pyarrow as pa
from deltalake import DeltaTable, write_deltalake
import lancedb

logger = logging.getLogger(__name__)


class ProductImageLinker:
    """Links images to products using CSV mappings and Vision metadata"""

    def __init__(
        self,
        products_delta_path: Path,
        lakehouse_lance_path: Path,
        csv_mappings_dir: Path
    ):
        self.products_path = Path(products_delta_path)
        self.lance_path = Path(lakehouse_lance_path)
        self.csv_dir = Path(csv_mappings_dir)

    def load_products(self) -> pd.DataFrame:
        """Load products from Delta table"""
        dt = DeltaTable(str(self.products_path))
        df = dt.to_pandas()
        logger.info(f"Loaded {len(df)} products")
        return df

    def load_image_metadata(self) -> pd.DataFrame:
        """Load Vision API metadata from LanceDB"""
        db = lancedb.connect(str(self.lance_path))
        table = db.open_table('embeddings')
        df = table.to_pandas()

        # Filter to images only
        images = df[df['filename'].str.contains('\.jpg|\.png', case=False, na=False)].copy()

        logger.info(f"Loaded {len(images)} image embeddings with Vision metadata")
        return images

    def load_csv_mappings(self) -> Dict[str, pd.DataFrame]:
        """Load all CSV mapping files"""
        mappings = {}

        csv_files = {
            'main_images': 'MediaAssets_main_image.csv',
            'other_images': 'MediaAssets_other_images.csv',
            'documents': 'MediaDocuments.csv',
            'documents_all': 'MediaDocuments_All.csv'
        }

        for key, filename in csv_files.items():
            csv_path = self.csv_dir / filename
            if csv_path.exists():
                try:
                    df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
                    mappings[key] = df
                    logger.info(f"Loaded {key}: {len(df)} mappings")
                except Exception as e:
                    logger.warning(f"Failed to load {filename}: {e}")

        return mappings

    def create_product_images_table(
        self,
        products: pd.DataFrame,
        images: pd.DataFrame,
        csv_mappings: Dict[str, pd.DataFrame],
        output_path: Path
    ):
        """
        Create product_images table linking products to images.

        Schema:
        - product_id (supplier_pid from catalog)
        - image_filename
        - image_type (main, additional, detail)
        - view_orientation (from Vision API)
        - view_perspective (from Vision API)
        - seo_description (from Vision API)
        - visible_specs (from Vision API)
        - image_url (MinIO or external)
        - embedding_id (link to LanceDB)
        """
        records = []

        # Process main images
        if 'main_images' in csv_mappings:
            main_df = csv_mappings['main_images']

            for _, row in main_df.iterrows():
                catalog_num = str(row.get('Catalog Number', '')).strip()
                image_file = str(row.get('File name', '')).strip()
                doc_id = str(row.get('Document Identifier', '')).strip()

                if not catalog_num or not image_file:
                    continue

                # Find Vision metadata for this image
                vision_meta = self._find_vision_metadata(images, image_file)

                record = {
                    'product_id': catalog_num,
                    'image_filename': image_file,
                    'image_type': 'main',
                    'view_orientation': vision_meta.get('orientation', 'unknown'),
                    'view_perspective': vision_meta.get('perspective', 'center'),
                    'seo_description': vision_meta.get('seo_description', f'Product image: {catalog_num}'),
                    'visible_specs': vision_meta.get('specs', ''),
                    'image_url': doc_id if doc_id.startswith('http') else f's3://customer-eaton/{image_file}',
                    'embedding_chunk_id': vision_meta.get('chunk_id', ''),
                    'has_vision_metadata': vision_meta.get('has_metadata', False)
                }

                records.append(record)

        # Process additional images
        if 'other_images' in csv_mappings:
            other_df = csv_mappings['other_images']

            for _, row in other_df.iterrows():
                catalog_num = str(row.get('Catalog Number', '')).strip()
                image_file = str(row.get('File name', '')).strip()

                if not catalog_num or not image_file:
                    continue

                vision_meta = self._find_vision_metadata(images, image_file)

                record = {
                    'product_id': catalog_num,
                    'image_filename': image_file,
                    'image_type': 'additional',
                    'view_orientation': vision_meta.get('orientation', 'unknown'),
                    'view_perspective': vision_meta.get('perspective', 'center'),
                    'seo_description': vision_meta.get('seo_description', f'Additional view: {catalog_num}'),
                    'visible_specs': vision_meta.get('specs', ''),
                    'image_url': row.get('Document Identifier', f's3://customer-eaton/{image_file}'),
                    'embedding_chunk_id': vision_meta.get('chunk_id', ''),
                    'has_vision_metadata': vision_meta.get('has_metadata', False)
                }

                records.append(record)

        logger.info(f"Created {len(records)} product-image links")

        # Write to Delta Lake
        if records:
            schema = pa.schema([
                ('product_id', pa.string()),
                ('image_filename', pa.string()),
                ('image_type', pa.string()),
                ('view_orientation', pa.string()),
                ('view_perspective', pa.string()),
                ('seo_description', pa.string()),
                ('visible_specs', pa.string()),
                ('image_url', pa.string()),
                ('embedding_chunk_id', pa.string()),
                ('has_vision_metadata', pa.bool_()),
            ])

            table = pa.Table.from_pylist(records, schema=schema)
            write_deltalake(str(output_path), table, mode="overwrite")

            logger.info(f"✓ Exported {len(records)} image links to {output_path}")

        return records

    def _find_vision_metadata(self, images: pd.DataFrame, image_filename: str) -> Dict:
        """Find Vision API metadata for an image"""
        # Match by filename (handle various formats)
        base_name = Path(image_filename).stem

        matches = images[images['filename'].str.contains(base_name, case=False, na=False)]

        if len(matches) == 0:
            return {'has_metadata': False}

        # Get first match
        meta = matches.iloc[0]
        text = meta['text']

        # Parse Vision API text format
        result = {
            'has_metadata': True,
            'chunk_id': f"{meta['document_id']}_{meta['chunk_index']}",
            'orientation': 'unknown',
            'perspective': 'center',
            'seo_description': '',
            'specs': ''
        }

        # Extract from formatted text
        for line in text.split('\n'):
            if 'VIEW ORIENTATION:' in line:
                result['orientation'] = line.split(':')[1].strip().lower().replace(' ', '_')
            elif 'VIEW PERSPECTIVE:' in line:
                result['perspective'] = line.split(':')[1].strip().lower()
            elif 'DESCRIPTION:' in line:
                result['seo_description'] = line.split(':', 1)[1].strip()
            elif 'VISIBLE SPECIFICATIONS:' in line:
                # Collect next few lines
                specs_lines = []
            elif line.strip().startswith('Current Rating:') or line.strip().startswith('Voltage:'):
                result['specs'] += line.strip() + '; '

        return result


# CLI entry point
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: python product_image_linker.py <products_delta> <lakehouse_lance> <csv_dir> [output]")
        sys.exit(1)

    products_path = Path(sys.argv[1])
    lance_path = Path(sys.argv[2])
    csv_dir = Path(sys.argv[3])
    output_path = Path(sys.argv[4]) if len(sys.argv) > 4 else Path("/tmp/product_images_delta")

    linker = ProductImageLinker(products_path, lance_path, csv_dir)

    products = linker.load_products()
    images = linker.load_image_metadata()
    csv_mappings = linker.load_csv_mappings()

    records = linker.create_product_images_table(products, images, csv_mappings, output_path)

    print(f"\n✓ Created {len(records)} product-image links")
    print(f"✓ Exported to {output_path}")

    # Show sample
    if records:
        import json
        print("\nSample link:")
        print(json.dumps(records[0], indent=2))
