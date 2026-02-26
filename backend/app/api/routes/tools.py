import base64
import logging
import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Body, Response
from pydantic import BaseModel
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tools", tags=["Tools"])

class ScreenshotAnalyzeRequest(BaseModel):
    image_base64: str

class ScreenshotAnalyzeResponse(BaseModel):
    status: str
    detected_location: Optional[str] = None
    context: Optional[str] = None
    error: Optional[str] = None

@router.options("/analyze-screenshot")
async def analyze_screenshot_options(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Timezone-Offset, X-Timezone-Id, X-Test-Bypass-Token"
    return {}

@router.post("/analyze-screenshot", response_model=ScreenshotAnalyzeResponse)
async def analyze_screenshot(request: ScreenshotAnalyzeRequest):
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
        img_data = request.image_base64
        if ',' in img_data:
            img_data = img_data.split(',')[1]

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
            "data": img_data
        }
        
        response = await model.generate_content_async([prompt, image_part])
        
        result_json_str = response.text.strip()
        
        # Strip potential markdown blocks sometimes returned by LLMs
        if result_json_str.startswith("```json"):
            result_json_str = result_json_str[7:-3]
        elif result_json_str.startswith("```"):
            result_json_str = result_json_str[3:-3]
            
        import json
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
