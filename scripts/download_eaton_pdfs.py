#!/usr/bin/env python3
"""
Download Eaton Technical Documentation

Downloads:
1. PDFs linked in BMEcat mime_sources (product-specific docs)
2. Official Eaton catalogs (general documentation)

All PDFs are downloaded, processed, and added to lakehouse for RAG.
"""

import asyncio
import logging
import sys
from pathlib import Path
import json
import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

from deltalake import DeltaTable

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EatonPDFDownloader:
    """Download Eaton technical PDFs"""

    def __init__(self, output_dir: Path = Path("/tmp/eaton_pdfs")):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Official Eaton catalogs
        self.official_catalogs = [
            {
                "name": "xEffect_Complete_Catalog",
                "url": "https://www.eaton.com/content/dam/eaton/products/low-voltage-power-distribution-control-systems/circuit-breakers/miniature-circuit-breakers-supplementary-protectors/xeffect-miniature-circuit-breakers/eaton-xeffect-complete-catalog-ca003002en.pdf",
                "size_mb": 57,
                "description": "Complete xEffect miniature circuit breaker catalog"
            },
            {
                "name": "FAZ6_Series_Datasheet",
                "url": "https://www.eaton.com/content/dam/eaton/products/low-voltage-power-distribution-control-systems/circuit-breakers/miniature-circuit-breakers-supplementary-protectors/faz-miniature-circuit-breakers/eaton-faz6-miniature-circuit-breaker-data-sheet-td025011en.pdf",
                "size_mb": 2,
                "description": "FAZ6 miniature circuit breakers technical data"
            },
            {
                "name": "FRCdM_Installation_Guide",
                "url": "https://www.eaton.com/content/dam/eaton/products/low-voltage-power-distribution-control-systems/circuit-breakers/residual-current-devices/frcdm-residual-current-devices/eaton-frcdm-rcd-installation-guide-ig025001en.pdf",
                "size_mb": 4,
                "description": "FRCdM residual current device installation guide"
            },
            {
                "name": "FRBdM_Technical_Specs",
                "url": "https://www.eaton.com/content/dam/eaton/products/low-voltage-power-distribution-control-systems/circuit-breakers/residual-current-circuit-breakers/frbdm-rccbs/eaton-frbdm-rcbo-technical-specifications-ts025002en.pdf",
                "size_mb": 3,
                "description": "FRBdM RCBO technical specifications"
            },
        ]

    def extract_bmecat_pdf_urls(self, products_delta_path: Path) -> list[dict]:
        """Extract PDF URLs from BMEcat product data"""
        try:
            dt = DeltaTable(str(products_delta_path))
            df = dt.to_pandas()

            pdf_refs = []
            for _, row in df.iterrows():
                mime_sources_json = row['mime_sources']
                if not mime_sources_json:
                    continue

                sources = json.loads(mime_sources_json)
                for source in sources:
                    if isinstance(source, str) and '.pdf' in source.lower() and source.startswith('http'):
                        pdf_refs.append({
                            'product_id': row['supplier_pid'],
                            'product_name': row['product_name'],
                            'url': source,
                            'type': 'product_specific'
                        })

            logger.info(f"Found {len(pdf_refs)} PDF links in BMEcat for {len(set(r['product_id'] for r in pdf_refs))} products")
            return pdf_refs

        except Exception as e:
            logger.error(f"Failed to extract BMEcat PDFs: {e}")
            return []

    async def download_pdf(self, url: str, filename: str) -> bool:
        """Download single PDF"""
        output_path = self.output_dir / filename

        if output_path.exists():
            logger.info(f"✓ Already exists: {filename}")
            return True

        try:
            logger.info(f"Downloading: {filename} from {url[:80]}...")

            async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
                response = await client.get(url)

                if response.status_code != 200:
                    logger.error(f"Failed to download {filename}: HTTP {response.status_code}")
                    return False

                # Save PDF
                with open(output_path, 'wb') as f:
                    f.write(response.content)

                size_mb = len(response.content) / 1024 / 1024
                logger.info(f"✓ Downloaded: {filename} ({size_mb:.2f} MB)")
                return True

        except Exception as e:
            logger.error(f"Download failed for {filename}: {e}")
            return False

    async def download_all(self, products_delta_path: Path = None):
        """Download all PDFs (BMEcat + official catalogs)"""
        logger.info("="*70)
        logger.info("EATON PDF DOWNLOAD")
        logger.info("="*70)

        downloaded = []
        failed = []

        # Download official catalogs
        logger.info(f"\nDownloading {len(self.official_catalogs)} official catalogs...")
        for catalog in self.official_catalogs:
            filename = f"{catalog['name']}.pdf"
            success = await self.download_pdf(catalog['url'], filename)
            if success:
                downloaded.append(filename)
            else:
                failed.append(filename)

        # Download BMEcat PDFs
        if products_delta_path and products_delta_path.exists():
            logger.info("\nExtracting PDF links from BMEcat...")
            bmecat_pdfs = self.extract_bmecat_pdf_urls(products_delta_path)

            logger.info(f"Downloading {len(bmecat_pdfs)} product-specific PDFs...")
            for i, pdf_ref in enumerate(bmecat_pdfs[:20], 1):  # Limit to first 20
                filename = f"product_{pdf_ref['product_id']}_{i}.pdf"
                success = await self.download_pdf(pdf_ref['url'], filename)
                if success:
                    downloaded.append(filename)
                else:
                    failed.append(filename)

        # Summary
        logger.info("\n" + "="*70)
        logger.info("DOWNLOAD COMPLETE")
        logger.info("="*70)
        logger.info(f"  Downloaded: {len(downloaded)}")
        logger.info(f"  Failed: {len(failed)}")
        logger.info(f"  Output: {self.output_dir}")
        logger.info("="*70)

        return downloaded, failed


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Download Eaton technical PDFs")
    parser.add_argument(
        "--products-delta",
        default="data/lakehouse/eaton/delta/eaton_products",
        help="Path to eaton_products Delta table"
    )
    parser.add_argument(
        "--output",
        default="/tmp/eaton_pdfs",
        help="Output directory for PDFs"
    )
    parser.add_argument(
        "--official-only",
        action="store_true",
        help="Download only official catalogs (not product-specific PDFs)"
    )
    args = parser.parse_args()

    downloader = EatonPDFDownloader(output_dir=Path(args.output))

    if args.official_only:
        logger.info("Downloading official catalogs only...")
        downloaded = []
        for catalog in downloader.official_catalogs:
            filename = f"{catalog['name']}.pdf"
            success = await downloader.download_pdf(catalog['url'], filename)
            if success:
                downloaded.append(filename)
        print(f"\n✓ Downloaded {len(downloaded)} official catalogs to {args.output}")
    else:
        products_path = Path(args.products_delta) if not args.official_only else None
        downloaded, failed = await downloader.download_all(products_path)

    print(f"\n✓ PDFs ready in: {args.output}")
    print(f"  Next: Upload to MinIO and trigger ingestion")


if __name__ == "__main__":
    asyncio.run(main())
