"""
KadriX Media Service
Handles video upload and analysis
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import uuid
import logging

app = FastAPI(title="KadriX Media Service", version="1.0.0")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory for storing uploaded videos
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_UPLOAD_SIZE_BYTES = 200 * 1024 * 1024
UPLOAD_CHUNK_SIZE_BYTES = 1024 * 1024

# Response Models
class MediaUploadResponse(BaseModel):
    file_id: str
    filename: str
    file_url: str
    internal_file_path: str
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
    Persists the file to disk and returns metadata for later rendering
    """
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
    
    # Create unique filename
    stored_filename = f"{file_id}.{file_extension}"
    file_path = UPLOAD_DIR / stored_filename
    logger.info(
        "Received media upload: original_filename=%s content_type=%s stored_filename=%s file_id=%s",
        file.filename,
        file.content_type,
        stored_filename,
        file_id,
    )
    
    # Save uploaded file to disk while enforcing the upload limit.
    try:
        total_size = 0
        with open(file_path, "wb") as buffer:
            while chunk := file.file.read(UPLOAD_CHUNK_SIZE_BYTES):
                total_size += len(chunk)
                if total_size > MAX_UPLOAD_SIZE_BYTES:
                    buffer.close()
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail="Video file is too large. Maximum upload size is 200MB."
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {str(e)}"
        )
    
    # Get file size
    file_size = file_path.stat().st_size
    logger.info(
        "Media upload persisted: path=%s exists=%s size_bytes=%s",
        file_path,
        file_path.exists(),
        file_size,
    )
    
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
    
    # Construct URLs for accessing the file
    file_url = f"/api/media/assets/{stored_filename}"
    internal_file_path = f"/app/uploads/{stored_filename}"
    
    response = MediaUploadResponse(
        file_id=file_id,
        filename=file.filename,
        file_url=file_url,
        internal_file_path=internal_file_path,
        size_bytes=file_size,
        format=file_extension,
        transcript=mock_transcript.strip(),
        product_context=mock_product_context.strip()
    )
    
    return response


@app.get("/media/assets/{filename}")
async def get_media_asset(filename: str, request: Request):
    """
    Serve uploaded video files
    """
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Media file not found")
    
    return serve_video_file(file_path, filename, request)


def serve_video_file(file_path: Path, filename: str, request: Request):
    """
    Serve uploaded videos with HTTP Range support so browser video controls can seek.
    """
    file_size = file_path.stat().st_size
    range_header = request.headers.get("range")

    if not range_header:
        return FileResponse(
            path=file_path,
            media_type="video/mp4",
            filename=filename,
            headers={"Accept-Ranges": "bytes"},
        )

    try:
        range_unit, range_value = range_header.strip().split("=", 1)
        if range_unit != "bytes":
            raise ValueError("Only byte ranges are supported")

        start_text, end_text = range_value.split("-", 1)
        if start_text:
            start = int(start_text)
            end = int(end_text) if end_text else file_size - 1
        else:
            suffix_length = int(end_text)
            start = max(file_size - suffix_length, 0)
            end = file_size - 1

        end = min(end, file_size - 1)
        if start < 0 or start > end or start >= file_size:
            raise ValueError("Invalid byte range")
    except ValueError:
        return Response(
            status_code=416,
            headers={
                "Content-Range": f"bytes */{file_size}",
                "Accept-Ranges": "bytes",
            },
        )

    content_length = end - start + 1
    with open(file_path, "rb") as video_file:
        video_file.seek(start)
        data = video_file.read(content_length)

    return Response(
        content=data,
        status_code=206,
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Content-Length": str(content_length),
            "Content-Disposition": f'inline; filename="{filename}"',
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

# Made with Bob
