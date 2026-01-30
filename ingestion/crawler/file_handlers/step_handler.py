"""
STEP File Handler

Extracts metadata from STEP (.stp) 3D CAD files.

STEP format (ISO 10303) contains structured header with:
- Part numbers
- Dimensions
- Author/organization
- Creation date
"""

import logging
from pathlib import Path
from typing import Optional

from .base import BaseHandler

logger = logging.getLogger(__name__)


class STPHandler(BaseHandler):
    """
    Extract metadata from STEP file header.

    STEP files are 3D CAD models used in engineering.
    """

    @classmethod
    def supported_extensions(cls) -> set[str]:
        return {'.stp', '.step'}

    async def extract(self, path: Path) -> Optional[str]:
        """
        Extract metadata from STEP file header.

        STEP format has structured header:
        - FILE_DESCRIPTION
        - FILE_NAME (part number, author, organization)
        - FILE_SCHEMA
        """
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first 5000 bytes (header section)
                header = f.read(5000)

            # Extract key info
            lines = header.split('\n')

            metadata = {
                "filename": path.name,
                "file_type": "3D CAD Model (STEP)",
                "description": "",
                "part_number": "",
                "organization": "",
                "author": "",
                "schema": ""
            }

            for i, line in enumerate(lines[:100]):
                line_clean = line.strip()

                # Extract FILE_DESCRIPTION
                if "FILE_DESCRIPTION" in line_clean:
                    # Next lines usually have description
                    if i + 1 < len(lines):
                        desc_line = lines[i + 1].strip("();' ")
                        if desc_line:
                            metadata["description"] = desc_line

                # Extract FILE_NAME
                # Format: FILE_NAME('part.stp','2025-01-11','Author',('Organization'),'CAD','','');
                if "FILE_NAME" in line_clean:
                    parts = line_clean.split("'")
                    if len(parts) >= 3:
                        metadata["part_number"] = parts[1].replace('.stp', '').replace('.step', '')
                    if len(parts) >= 5:
                        metadata["author"] = parts[3]
                    if len(parts) >= 7:
                        metadata["organization"] = parts[5]

                # Extract FILE_SCHEMA
                if "FILE_SCHEMA" in line_clean:
                    if "(" in line_clean:
                        schema_parts = line_clean.split("(")
                        if len(schema_parts) > 1:
                            schema = schema_parts[1].split("'")[1] if "'" in schema_parts[1] else ""
                            metadata["schema"] = schema

            # Extract part number from filename if not in header
            if not metadata["part_number"]:
                # eaton-faz_mcb_1p-3d-model.stp → faz_mcb_1p
                name_parts = path.stem.replace("eaton-", "").replace("-3d-model", "").replace("_3d-model", "")
                metadata["part_number"] = name_parts.upper()

            # Set default organization
            if not metadata["organization"]:
                metadata["organization"] = "Eaton Industries"

            # Format for RAG
            text = f"""3D CAD MODEL: {path.name}

FILE TYPE: STEP (ISO 10303-21) - 3D Engineering Drawing
PART NUMBER: {metadata['part_number']}
ORGANIZATION: {metadata['organization']}
AUTHOR: {metadata['author'] or 'Engineering Team'}
SCHEMA: {metadata['schema'] or 'AP214 (Automotive Design)'}

DESCRIPTION: {metadata['description'] or 'Product 3D model for engineering and manufacturing'}

FORMAT DETAILS:
- Standard: ISO 10303 (STEP - Standard for the Exchange of Product model data)
- Application Protocol: AP214 (Core Data for Automotive Mechanical Design)
- Use Cases: Engineering analysis, manufacturing planning, technical documentation, CAD/CAM integration

COMPATIBLE SOFTWARE:
- SolidWorks, CATIA, Fusion 360, FreeCAD
- Siemens NX, Creo, Inventor
- Any CAD software supporting STEP format

DOWNLOAD: Available via MinIO object storage
FILE SIZE: {path.stat().st_size / 1024:.1f} KB

SEARCH KEYWORDS: 3D model, CAD, STEP, {metadata['part_number']}, engineering drawing, mechanical design
"""

            return text

        except Exception as e:
            logger.error(f"STEP extraction failed for {path.name}: {e}")
            # Return minimal info
            part_num = path.stem.replace("eaton-", "").replace("-3d-model", "").upper()
            return f"""3D CAD MODEL: {path.name}
FILE TYPE: STEP (ISO 10303) - 3D Engineering Drawing
PART NUMBER: {part_num}
ORGANIZATION: Eaton Industries

Download available via MinIO object storage.
Compatible with all major CAD software (SolidWorks, CATIA, Fusion 360, etc.)
"""
