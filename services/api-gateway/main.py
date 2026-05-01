"""
KadriX API Gateway
Main entry point for all client requests
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
from typing import Optional

app = FastAPI(title="KadriX API Gateway", version="1.0.0")

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
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": (file.filename, await file.read(), file.content_type)}
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Made with Bob
