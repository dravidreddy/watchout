import base64
import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Response, Request, Depends
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.firebase_auth import verify_firebase_token
from app.core.rate_limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["Tools"])

class ScreenshotAnalyzeRequest(BaseModel):
    image_base64: str = Field(..., max_length=6_000_000)

class ScreenshotAnalyzeResponse(BaseModel):
    status: str
    detected_location: Optional[str] = None
    context: Optional[str] = None
    error: Optional[str] = None

@router.options("/analyze-screenshot")
async def analyze_screenshot_options(response: Response):
    response.headers["Access-Control-Allow-Origin"] = settings.frontend_url
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Timezone-Offset, X-Timezone-Id, X-Test-Bypass-Token"
    return {}

@router.post("/analyze-screenshot", response_model=ScreenshotAnalyzeResponse)
@limiter.limit("8/minute")
async def analyze_screenshot(
    request: Request,
    payload: ScreenshotAnalyzeRequest,
    _token_data: dict = Depends(verify_firebase_token),
):
    """
    Analyzes an uploaded screenshot using Google Gemini 1.5 Flash 
    to extract travel destinations, landmarks, and context.
    """
    if not settings.gemini_api_key:
        logger.error("Gemini API key not configured for Vision analysis.")
        raise HTTPException(status_code=500, detail="Vision AI key not configured.")

    logger.info("Extracting location from screenshot via Gemini Vision.")

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        
        # Clean the base64 string if it contains the data uri prefix e.g 'data:image/jpeg;base64,'
        img_data = payload.image_base64
        if ',' in img_data:
            img_data = img_data.split(',')[1]

        # Validate base64 and enforce a hard decoded-size cap to prevent memory abuse.
        try:
            decoded = base64.b64decode(img_data, validate=True)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image payload")
        if len(decoded) > 4_000_000:
            raise HTTPException(status_code=413, detail="Image payload too large (max 4MB)")

        prompt = (
            "You are an expert travel destination identifier. "
            "Analyze this image and extract any visible text, hashtags, and visual landmarks to determine the travel destination. "
            "Return ONLY a valid JSON object in this exact format, with no markdown formatting or extra text: "
            '{"detected_location": "City, Country", "context": "hashtags/description"}. '
            "If no clear destination can be identified, return null for detected_location."
        )

        model = genai.GenerativeModel("gemini-1.5-flash")
        
        image_part = {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(decoded).decode("utf-8")
        }
        
        response = await model.generate_content_async([prompt, image_part])
        
        result_json_str = response.text.strip()
        
        # Strip potential markdown blocks sometimes returned by LLMs
        if result_json_str.startswith("```json"):
            result_json_str = result_json_str[7:-3]
        elif result_json_str.startswith("```"):
            result_json_str = result_json_str[3:-3]
            
        result = json.loads(result_json_str.strip())

        return ScreenshotAnalyzeResponse(
            status="success",
            detected_location=result.get("detected_location"),
            context=result.get("context")
        )

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error processing screenshot with Vision AI: {e}\n{error_trace}")
        raise HTTPException(status_code=500, detail="Failed to process image.")
