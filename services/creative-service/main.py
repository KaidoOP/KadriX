"""
KadriX Creative Service
Generates preview videos from campaign blueprints using text slides.
"""
from datetime import datetime
from typing import List, Optional
import uuid
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from moviepy.editor import (
    TextClip,
    ColorClip,
    CompositeVideoClip,
    concatenate_videoclips,
)

app = FastAPI(title="KadriX Creative Service", version="1.0.0")

# Directory for storing generated videos
OUTPUT_DIR = Path("/app/output")
OUTPUT_DIR.mkdir(exist_ok=True)


class StoryboardScene(BaseModel):
    timestamp: str
    scene_title: str
    visual_direction: str
    narration: str


class RenderPreviewVideoRequest(BaseModel):
    campaign_id: str
    main_hook: str
    voiceover_script: str
    video_concept: str
    storyboard_scenes: List[StoryboardScene]
    mood_direction: str
    music_direction: str
    visual_style: str
    call_to_action: str


class RenderPreviewVideoResponse(BaseModel):
    campaign_id: str
    video_url: str
    filename: str
    duration_seconds: float
    status: str


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "creative-service",
        "version": "1.0.0",
    }


@app.post("/creative/render-preview-video", response_model=RenderPreviewVideoResponse)
async def render_preview_video(request: RenderPreviewVideoRequest):
    """
    Generate a simple MP4 preview video from campaign blueprint text slides.
    
    This is a hackathon-safe implementation:
    - Uses text slides only (no external assets)
    - No copyrighted music (silent video)
    - No IBM credentials required
    - Local rendering with MoviePy
    """
    try:
        # Generate unique filename
        video_id = str(uuid.uuid4())[:8]
        filename = f"preview_{request.campaign_id}_{video_id}.mp4"
        output_path = OUTPUT_DIR / filename
        
        # Create video clips
        clips = []
        
        # Intro slide with main hook
        intro_clip = create_text_slide(
            title="Campaign Preview",
            content=request.main_hook,
            duration=4.0,
            bg_color=(20, 30, 50),
            title_color="white",
            content_color="lightblue",
        )
        clips.append(intro_clip)
        
        # Storyboard scene slides
        for scene in request.storyboard_scenes:
            scene_clip = create_scene_slide(
                timestamp=scene.timestamp,
                scene_title=scene.scene_title,
                visual_direction=scene.visual_direction,
                narration=scene.narration,
                duration=5.0,
            )
            clips.append(scene_clip)
        
        # Final slide with call to action
        cta_clip = create_text_slide(
            title="Call to Action",
            content=request.call_to_action,
            duration=4.0,
            bg_color=(30, 50, 70),
            title_color="white",
            content_color="lightgreen",
        )
        clips.append(cta_clip)
        
        # Concatenate all clips
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Write video file (silent, no audio)
        final_video.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio=False,
            preset="ultrafast",
            logger=None,
        )
        
        # Clean up clips
        for clip in clips:
            clip.close()
        final_video.close()
        
        # Calculate duration
        duration = sum(clip.duration for clip in clips)
        
        # Return response
        video_url = f"/api/creative/assets/{filename}"
        
        return RenderPreviewVideoResponse(
            campaign_id=request.campaign_id,
            video_url=video_url,
            filename=filename,
            duration_seconds=round(duration, 2),
            status="generated",
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Video generation failed: {str(e)}",
        )


@app.get("/creative/assets/{filename}")
async def get_asset(filename: str):
    """
    Serve generated video files.
    """
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=filename,
    )


def create_text_slide(
    title: str,
    content: str,
    duration: float,
    bg_color: tuple = (30, 30, 30),
    title_color: str = "white",
    content_color: str = "lightgray",
) -> CompositeVideoClip:
    """
    Create a simple text slide with title and content.
    """
    width, height = 1280, 720
    
    # Create background using ColorClip
    bg = ColorClip(
        size=(width, height),
        color=bg_color,
    ).set_duration(duration)
    
    # Create title
    title_clip = TextClip(
        wrap_text(title, 40),
        fontsize=48,
        color=title_color,
        font="DejaVu-Sans-Bold",
        method="caption",
        size=(width - 100, None),
    ).set_position(("center", 150)).set_duration(duration)
    
    # Create content
    content_clip = TextClip(
        wrap_text(content, 60),
        fontsize=32,
        color=content_color,
        font="DejaVu-Sans",
        method="caption",
        size=(width - 150, None),
    ).set_position(("center", 300)).set_duration(duration)
    
    # Composite
    return CompositeVideoClip([bg, title_clip, content_clip], size=(width, height))


def create_scene_slide(
    timestamp: str,
    scene_title: str,
    visual_direction: str,
    narration: str,
    duration: float,
) -> CompositeVideoClip:
    """
    Create a storyboard scene slide.
    """
    width, height = 1280, 720
    
    # Create background using ColorClip
    bg = ColorClip(
        size=(width, height),
        color=(25, 35, 45),
    ).set_duration(duration)
    
    # Timestamp
    timestamp_clip = TextClip(
        timestamp,
        fontsize=28,
        color="yellow",
        font="DejaVu-Sans-Bold",
    ).set_position((50, 50)).set_duration(duration)
    
    # Scene title
    title_clip = TextClip(
        wrap_text(scene_title, 40),
        fontsize=42,
        color="white",
        font="DejaVu-Sans-Bold",
        method="caption",
        size=(width - 100, None),
    ).set_position(("center", 120)).set_duration(duration)
    
    # Visual direction label
    visual_label = TextClip(
        "Visual:",
        fontsize=24,
        color="lightblue",
        font="DejaVu-Sans-Bold",
    ).set_position((100, 250)).set_duration(duration)
    
    # Visual direction content
    visual_clip = TextClip(
        wrap_text(visual_direction, 70),
        fontsize=24,
        color="lightgray",
        font="DejaVu-Sans",
        method="caption",
        size=(width - 200, None),
    ).set_position((100, 290)).set_duration(duration)
    
    # Narration label
    narration_label = TextClip(
        "Narration:",
        fontsize=24,
        color="lightgreen",
        font="DejaVu-Sans-Bold",
    ).set_position((100, 450)).set_duration(duration)
    
    # Narration content
    narration_clip = TextClip(
        wrap_text(narration, 70),
        fontsize=24,
        color="lightgray",
        font="DejaVu-Sans",
        method="caption",
        size=(width - 200, None),
    ).set_position((100, 490)).set_duration(duration)
    
    # Composite
    return CompositeVideoClip(
        [bg, timestamp_clip, title_clip, visual_label, visual_clip, narration_label, narration_clip],
        size=(width, height),
    )


def wrap_text(text: str, max_chars: int) -> str:
    """
    Wrap text to fit within max_chars per line.
    """
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        word_length = len(word)
        if current_length + word_length + len(current_line) <= max_chars:
            current_line.append(word)
            current_length += word_length
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = word_length
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return "\n".join(lines)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8004)


# Made with Bob