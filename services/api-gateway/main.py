"""
KadriX API Gateway
Main entry point for all client requests
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import logging
from typing import Optional

app = FastAPI(title="KadriX API Gateway", version="1.0.0")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs from environment variables
CAMPAIGN_SERVICE_URL = os.getenv("CAMPAIGN_SERVICE_URL", "http://campaign-service:8001")
MEDIA_SERVICE_URL = os.getenv("MEDIA_SERVICE_URL", "http://media-service:8002")
FEEDBACK_SERVICE_URL = os.getenv("FEEDBACK_SERVICE_URL", "http://feedback-service:8003")
CREATIVE_SERVICE_URL = os.getenv("CREATIVE_SERVICE_URL", "http://creative-service:8004")
MAX_MEDIA_UPLOAD_SIZE_BYTES = 200 * 1024 * 1024

# Request/Response Models
class CampaignGenerateRequest(BaseModel):
    product_idea: str
    description: str
    campaign_goal: str
    target_audience: str
    tone: str
    video_context: Optional[str] = None

class CampaignImproveRequest(BaseModel):
    campaign_id: str
    original_campaign: dict
    feedback: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "1.0.0"
    }

@app.post("/api/campaigns/generate")
async def generate_campaign(request: CampaignGenerateRequest):
    """
    Generate a new marketing campaign
    Proxies request to campaign-service
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{CAMPAIGN_SERVICE_URL}/campaigns/generate",
                json=request.dict()
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Campaign service error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Campaign service unavailable: {str(e)}"
        )

@app.post("/api/campaigns/improve")
async def improve_campaign(request: CampaignImproveRequest):
    """
    Improve an existing campaign based on feedback
    Proxies request to feedback-service
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{FEEDBACK_SERVICE_URL}/feedback/improve",
                json=request.dict()
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Feedback service error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Feedback service unavailable: {str(e)}"
        )

@app.post("/api/media/upload")
async def upload_media(file: UploadFile = File(...)):
    """
    Upload video file for analysis
    Proxies request to media-service
    """
    try:
        upload_bytes = await file.read()
        if len(upload_bytes) > MAX_MEDIA_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Video file is too large. Maximum upload size is 200MB."
            )

        async with httpx.AsyncClient(timeout=180.0) as client:
            files = {"file": (file.filename, upload_bytes, file.content_type)}
            response = await client.post(
                f"{MEDIA_SERVICE_URL}/media/upload",
                files=files
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Media service error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Media service unavailable: {str(e)}"
        )

@app.post("/api/creative/render-preview-video")
async def render_preview_video(request: dict):
    """
    Generate preview video from campaign blueprint
    Proxies request to creative-service
    """
    try:
        logger.info(
            "Forwarding creative render request: source_video_url=%s source_video_path=%s source_file_id=%s",
            request.get("source_video_url"),
            request.get("source_video_path"),
            request.get("source_file_id"),
        )
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{CREATIVE_SERVICE_URL}/creative/render-preview-video",
                json=request
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Creative service error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Creative service unavailable: {str(e)}"
        )

def build_asset_response(response: httpx.Response, filename: str) -> Response:
    """Return proxied video bytes while preserving headers needed for seeking."""
    passthrough_headers = {}
    for header_name in (
        "accept-ranges",
        "content-range",
        "content-length",
        "content-disposition",
    ):
        header_value = response.headers.get(header_name)
        if header_value:
            passthrough_headers[header_name] = header_value

    passthrough_headers.setdefault("accept-ranges", "bytes")
    passthrough_headers.setdefault("content-disposition", f'inline; filename="{filename}"')

    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type", "video/mp4"),
        headers=passthrough_headers,
    )


@app.get("/api/creative/assets/{filename}")
async def get_creative_asset(filename: str, request: Request):
    """
    Get generated video file
    Proxies request to creative-service
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {}
            if range_header := request.headers.get("range"):
                headers["Range"] = range_header

            response = await client.get(
                f"{CREATIVE_SERVICE_URL}/creative/assets/{filename}",
                headers=headers,
            )
            response.raise_for_status()
            return build_asset_response(response, filename)
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Creative service error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Creative service unavailable: {str(e)}"
        )

@app.get("/api/media/assets/{filename}")
async def get_media_asset(filename: str, request: Request):
    """
    Get uploaded media file
    Proxies request to media-service
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {}
            if range_header := request.headers.get("range"):
                headers["Range"] = range_header

            response = await client.get(
                f"{MEDIA_SERVICE_URL}/media/assets/{filename}",
                headers=headers,
            )
            response.raise_for_status()
            return build_asset_response(response, filename)
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Media service error: {e.response.text}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Media service unavailable: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Made with Bob
