"""
Real-Time Claude-Powered Data Analysis
Uses Claude Sonnet 4.5 to analyze uploaded files and provide business insights
"""
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict
import anthropic
import logging
import os
from minio import Minio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/claude-analysis", tags=["claude-analysis"])


class AnalysisRequest(BaseModel):
    customer_id: str
    minio_bucket: str


def get_minio():
    return Minio(
        endpoint="localhost:4050",
        access_key="0711admin",
        secret_key="0711secret",
        secure=False
    )


BUSINESS_ANALYST_PROMPT = """You are a neutral data analyst reviewing uploaded business files.

Analyze the file inventory objectively and provide:

1. DATA OVERVIEW
   - What types of files are present
   - What business domains they cover
   - Overall data quality and completeness

2. POTENTIAL USE CASES
   - What processes this data could support
   - What questions it could answer
   - What systems it could integrate with

3. DATA GAPS
   - What's missing for comprehensive analysis
   - What additional data would be valuable
   - What quality issues exist

4. REALISTIC OPPORTUNITIES
   - Process automation possibilities (with realistic scope)
   - Integration opportunities
   - Analysis capabilities enabled

Be factual, neutral, and specific. Avoid hype. Focus on practical applications and realistic benefits."""


async def analyze_files_with_claude(customer_id: str, bucket_name: str) -> Dict:
    """
    Use Claude to analyze actual uploaded files and provide business insights
    """
    from api.config import settings

    logger.info(f"🧠 Starting Claude analysis for {customer_id}")

    try:
        # Get Anthropic API key from settings
        api_key = settings.anthropic_api_key
        if not api_key:
            logger.warning(f"No anthropic_api_key in settings (checked: {api_key is None})")
            return {"mock": True, "error": "No API key configured"}

        client = anthropic.Anthropic(api_key=api_key)
        minio = get_minio()

        # Get list of files from MinIO
        objects = list(minio.list_objects(bucket_name=bucket_name, recursive=True))

        # Sample files for analysis (first 50)
        sampled_files = objects[:50]

        # Build file inventory for Claude
        file_inventory = []
        for obj in sampled_files:
            file_type = obj.object_name.split('.')[-1] if '.' in obj.object_name else 'unknown'
            file_inventory.append({
                "name": obj.object_name[16:],  # Remove timestamp
                "size_mb": round(obj.size / 1024 / 1024, 2),
                "type": file_type
            })

        # Prepare prompt for Claude
        analysis_prompt = f"""DATA ANALYSIS REQUEST

Customer: {customer_id.upper()}
Total files uploaded: {len(objects)}
Analyzing sample: {len(sampled_files)} files

FILE INVENTORY:
{chr(10).join([f"- {f['name']} ({f['size_mb']} MB, .{f['type']})" for f in file_inventory[:30]])}
{f"... plus {len(file_inventory) - 30} more files" if len(file_inventory) > 30 else ""}

NOTABLE FILES:
{chr(10).join([f"- {f['name']} ({f['size_mb']} MB)" for f in file_inventory if f['size_mb'] > 1 or 'eclass' in f['name'].lower() or 'catalog' in f['name'].lower() or 'extract' in f['name'].lower()][:10])}

Please provide a neutral analysis:

1. What types of business data is present here?
2. What processes or systems might this data support?
3. What questions could be answered with this data?
4. What are realistic automation or analysis opportunities?
5. What additional context or data would be helpful?

Be specific and factual. Focus on practical applications."""

        # Call Claude
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=BUSINESS_ANALYST_PROMPT,
            messages=[{
                "role": "user",
                "content": analysis_prompt
            }]
        )

        analysis_text = message.content[0].text

        logger.info(f"✓ Claude analysis complete for {customer_id}")

        return {
            "success": True,
            "customer_id": customer_id,
            "files_analyzed": len(sampled_files),
            "total_files": len(objects),
            "analysis": analysis_text,
            "model": "claude-sonnet-4-20250514"
        }

    except Exception as e:
        logger.error(f"Claude analysis failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/analyze")
async def trigger_claude_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger Claude analysis of uploaded files
    Returns immediately, processes in background
    """
    logger.info(f"Triggering Claude analysis for {request.customer_id}")

    # Start analysis in background
    background_tasks.add_task(
        analyze_files_with_claude,
        request.customer_id,
        request.minio_bucket
    )

    return {
        "success": True,
        "message": "Claude analysis started",
        "customer_id": request.customer_id
    }


@router.get("/result/{customer_id}")
async def get_analysis_result(customer_id: str):
    """
    Get Claude analysis result for customer
    """
    # Would retrieve from cache/database
    # For now, trigger fresh analysis
    result = await analyze_files_with_claude(customer_id, f"customer-{customer_id}")

    return result
