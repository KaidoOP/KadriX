"""
KadriX Media Service
Handles video upload and analysis
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

app = FastAPI(title="KadriX Media Service", version="1.0.0")

# Response Models
class MediaUploadResponse(BaseModel):
    file_id: str
    filename: str
    size_bytes: int
    format: str
    transcript: str
    product_context: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "media-service",
        "version": "1.0.0"
    }

@app.post("/media/upload", response_model=MediaUploadResponse)
async def upload_media(file: UploadFile = File(...)):
    """
    Upload and analyze video file
    Returns mock analysis for hackathon demo
    """
    # Read file to get size
    contents = await file.read()
    file_size = len(contents)
    
    # Validate file type (basic check)
    allowed_types = ["video/mp4", "video/mpeg", "video/quicktime", "video/x-msvideo"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Generate file ID
    file_id = str(uuid.uuid4())
    
    # Extract file extension
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "mp4"
    
    # Mock transcript and product context
    # In production, this would use IBM Watson Speech-to-Text
    mock_transcript = """
    [00:00] Hi everyone, welcome to our product demo.
    [00:05] Today I'm excited to show you our innovative solution.
    [00:10] This product is designed to help busy professionals save time.
    [00:15] It features an intuitive interface and powerful automation.
    [00:20] Let me walk you through the key features.
    [00:25] First, you'll notice the clean, modern design.
    [00:30] Everything is just a click away.
    [00:35] Thank you for watching, and I hope you're as excited as we are!
    """
    
    mock_product_context = """
    Product Type: Software/SaaS solution
    Target Audience: Busy professionals and small business owners
    Key Features Mentioned:
    - Intuitive interface
    - Powerful automation
    - Time-saving capabilities
    - Modern design
    - Easy to use
    
    Tone: Professional, enthusiastic, friendly
    Duration: Approximately 35-40 seconds
    Visual Style: Product demo with presenter
    """
    
    response = MediaUploadResponse(
        file_id=file_id,
        filename=file.filename,
        size_bytes=file_size,
        format=file_extension,
        transcript=mock_transcript.strip(),
        product_context=mock_product_context.strip()
    )
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

# Made with Bob
