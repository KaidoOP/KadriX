"""
KadriX Creative Service
Generates preview videos from campaign blueprints.
Can use uploaded demo videos as visual source or fall back to text slides.
"""
from datetime import datetime
from typing import List, Optional
import uuid
import os
from pathlib import Path
import textwrap
import io
import logging
from urllib.parse import unquote, urlparse

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    ImageClip, 
    VideoFileClip, 
    concatenate_videoclips, 
    CompositeVideoClip,
    AudioFileClip
)
import numpy as np

# MoviePy versions commonly used in lightweight demos still reference
# Image.ANTIALIAS, which was removed in newer Pillow releases.
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

# IBM Watson Text-to-Speech (optional)
try:
    from ibm_watson import TextToSpeechV1
    from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
    IBM_TTS_AVAILABLE = True
except ImportError:
    IBM_TTS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="KadriX Creative Service", version="1.0.0")

# Directories
OUTPUT_DIR = Path("/app/output")
OUTPUT_DIR.mkdir(exist_ok=True)
UPLOAD_DIR = Path("/app/uploads")

# Video dimensions
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
MIN_PREVIEW_DURATION_SECONDS = 0.0
VOICEOVER_END_PADDING_SECONDS = 1.0

# Environment variables for IBM TTS
USE_IBM_TTS = os.getenv("USE_IBM_TTS", "false").lower() == "true"
IBM_TTS_API_KEY = os.getenv("IBM_TTS_API_KEY", "")
IBM_TTS_URL = os.getenv("IBM_TTS_URL", "")
IBM_TTS_VOICE = os.getenv("IBM_TTS_VOICE", "en-US_MichaelV3Voice")


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
    # New fields for source video
    source_video_url: Optional[str] = None
    source_video_path: Optional[str] = None
    source_file_id: Optional[str] = None
    require_source_video: bool = False
    # TTS voice selection
    tts_voice: Optional[str] = None


class RenderPreviewVideoResponse(BaseModel):
    campaign_id: str
    video_url: str
    filename: str
    duration_seconds: float
    status: str
    used_source_video: bool
    render_mode: str  # "source_video" or "fallback_slides"
    voiceover_enabled: bool
    audio_filename: Optional[str] = None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "creative-service",
        "version": "1.0.0",
        "ibm_tts_available": IBM_TTS_AVAILABLE and USE_IBM_TTS,
    }


@app.post("/creative/render-preview-video", response_model=RenderPreviewVideoResponse)
async def render_preview_video(request: RenderPreviewVideoRequest):
    """
    Generate a preview video from campaign blueprint.
    
    If source video is available, uses real demo footage with overlays.
    Otherwise, falls back to text slide generation.
    """
    try:
        # Generate unique filename
        video_id = str(uuid.uuid4())[:8]
        filename = f"preview_{request.campaign_id}_{video_id}.mp4"
        output_path = OUTPUT_DIR / filename
        
        # Enhanced logging for source video debugging
        logger.info("=" * 60)
        logger.info("RENDER PREVIEW VIDEO REQUEST")
        logger.info(f"Campaign ID: {request.campaign_id}")
        logger.info(f"Source video URL: {request.source_video_url}")
        logger.info(f"Source video path: {request.source_video_path}")
        logger.info(f"Source file ID: {request.source_file_id}")
        logger.info(f"Require source video: {request.require_source_video}")
        
        # Check if source video is available
        source_video_file = find_source_video(request)
        used_source_video = source_video_file is not None
        render_mode = "source_video" if used_source_video else "fallback_slides"
        
        logger.info(f"resolved_source_path={source_video_file}")
        logger.info(f"file_exists={source_video_file.exists() if source_video_file else False}")
        logger.info(f"selected_render_mode={render_mode}")
        logger.info(f"Used source video: {used_source_video}")
        logger.info("=" * 60)

        if request.require_source_video and source_video_file is None:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Source video was required, but no uploaded file could be resolved. "
                    "Check source_video_url, source_video_path, source_file_id, and the shared media-uploads volume."
                ),
            )
        
        # Generate voiceover audio if enabled
        audio_file = None
        voiceover_enabled = False
        if USE_IBM_TTS and IBM_TTS_AVAILABLE and IBM_TTS_API_KEY:
            try:
                # Use voice from request or fall back to environment variable
                voice = request.tts_voice or IBM_TTS_VOICE
                audio_file = generate_voiceover(request.voiceover_script, video_id, voice=voice)
                voiceover_enabled = True
                logger.info(f"Generated voiceover audio with voice {voice}: {audio_file}")
            except Exception as e:
                logger.warning(f"Failed to generate voiceover: {e}")
                audio_file = None
        else:
            logger.info(
                "Skipping IBM TTS voiceover: use_ibm_tts=%s ibm_tts_sdk_available=%s has_api_key=%s has_service_url=%s voice=%s",
                USE_IBM_TTS,
                IBM_TTS_AVAILABLE,
                bool(IBM_TTS_API_KEY),
                bool(IBM_TTS_URL),
                request.tts_voice or IBM_TTS_VOICE,
            )
        
        if used_source_video:
            # Render with source video - modern SaaS ad style
            logger.info(f"Rendering modern SaaS ad with source video: {source_video_file}")
            final_video = render_with_source_video(
                source_video_file=source_video_file,
                request=request,
                audio_file=audio_file
            )
        else:
            # Fall back to slide-based rendering
            logger.info("Rendering with improved slides (no source video)")
            final_video = render_with_slides(request, audio_file)
        
        duration = final_video.duration
        has_audio_track = getattr(final_video, "audio", None) is not None

        # Write video file
        final_video.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio=has_audio_track,
            preset="ultrafast",
            logger=None,
        )
        
        # Clean up
        final_video.close()
        
        # Return response
        video_url = f"/api/creative/assets/{filename}"
        
        logger.info(
            "Video generation complete: filename=%s duration=%.2fs render_mode=%s voiceover_enabled=%s",
            filename,
            duration,
            render_mode,
            voiceover_enabled,
        )
        
        return RenderPreviewVideoResponse(
            campaign_id=request.campaign_id,
            video_url=video_url,
            filename=filename,
            duration_seconds=round(duration, 2),
            status="generated",
            used_source_video=used_source_video,
            render_mode=render_mode,
            voiceover_enabled=voiceover_enabled,
            audio_filename=audio_file.name if audio_file else None,
        )
        
    except Exception as e:
        logger.error(f"Video generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Video generation failed: {str(e)}",
        )


@app.get("/creative/assets/{filename}")
async def get_asset(filename: str, request: Request):
    """
    Serve generated video files.
    """
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return serve_video_file(file_path, filename, request)


def serve_video_file(file_path: Path, filename: str, request: Request):
    """
    Serve MP4 files with HTTP Range support so browser video controls can seek.
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


def find_source_video(request: RenderPreviewVideoRequest) -> Optional[Path]:
    """
    Find the source video file from the request parameters.
    """
    logger.info("Resolving source video")
    logger.info(f"UPLOAD_DIR: {UPLOAD_DIR} exists={UPLOAD_DIR.exists()}")

    def check_candidate(candidate: Path, reason: str) -> Optional[Path]:
        logger.info(f"Checking source candidate from {reason}: {candidate} exists={candidate.exists()}")
        if candidate.exists() and candidate.is_file():
            return candidate
        return None

    # Try source_video_path first (internal path). Only accept paths inside /app/uploads.
    if request.source_video_path:
        raw_path = unquote(request.source_video_path.strip())
        path = Path(raw_path)
        if raw_path.startswith("/app/uploads"):
            found = check_candidate(path, "source_video_path")
            if found:
                return found
        else:
            logger.warning(f"Ignoring source_video_path outside /app/uploads: {raw_path}")
    
    # Try to construct path from source_file_id
    if request.source_file_id:
        source_file_id = request.source_file_id.strip()
        for path in UPLOAD_DIR.glob(f"{source_file_id}.*"):
            found = check_candidate(path, "source_file_id glob")
            if found:
                return found
    
    # Try to extract filename from source_video_url
    if request.source_video_url:
        # Extract filename from URLs like /api/media/assets/abc123.mp4 or /media/assets/abc123.mp4.
        parsed_path = urlparse(request.source_video_url.strip()).path
        filename = unquote(parsed_path.rstrip("/").split("/")[-1])
        if filename:
            found = check_candidate(UPLOAD_DIR / filename, "source_video_url filename")
            if found:
                return found

    logger.info("No usable source video file found; falling back to slides")
    
    return None


def render_with_source_video(
    source_video_file: Path,
    request: RenderPreviewVideoRequest,
    audio_file: Optional[Path] = None
) -> VideoFileClip:
    """
    Render modern SaaS ad preview using the uploaded demo video as the main visual source.
    Creates a professional product launch ad with short overlays, not storyboard slides.
    """
    logger.info("Starting modern SaaS ad rendering...")
    
    # Load source video
    source_clip = VideoFileClip(str(source_video_file))
    logger.info(f"Source video loaded: {source_clip.duration:.2f}s, {source_clip.size}")
    
    # Target duration: 40-50 seconds for a modern ad
    target_duration = 45.0
    
    # Resize to 1280x720
    source_clip = source_clip.resize((VIDEO_WIDTH, VIDEO_HEIGHT))
    
    # Sample segments from the source video
    if source_clip.duration > target_duration:
        # Take segments from beginning, middle, and later middle
        segment_duration = target_duration / 3
        segments = [
            source_clip.subclip(0, segment_duration),
            source_clip.subclip(
                source_clip.duration / 2 - segment_duration / 2,
                source_clip.duration / 2 + segment_duration / 2
            ),
            source_clip.subclip(source_clip.duration - segment_duration, source_clip.duration)
        ]
        base_video = concatenate_videoclips(segments, method="compose")
        logger.info(f"Sampled {len(segments)} segments from source video")
    else:
        # Use the entire video, loop if too short
        if source_clip.duration < 30:
            loops_needed = int(30 / source_clip.duration) + 1
            base_video = concatenate_videoclips([source_clip] * loops_needed, method="compose")
            base_video = base_video.subclip(0, 30)
            logger.info(f"Looped short video {loops_needed} times")
        else:
            base_video = source_clip
            logger.info("Using full source video")
    
    # Generate product-specific overlays
    product_name = extract_product_name(request)
    overlay_texts = generate_overlay_copy(request, product_name)
    
    logger.info(f"Product: {product_name}")
    logger.info(f"Generated {len(overlay_texts)} overlay texts")
    
    # Create overlay clips - modern SaaS ad structure
    overlays = []
    
    # 0:00-0:03 - Intro hook card (short, punchy)
    intro_overlay = create_modern_hook_overlay(overlay_texts['hook'])
    intro_clip = ImageClip(intro_overlay).set_duration(3.0).set_position("center")
    overlays.append(intro_clip.set_start(0))
    logger.info("Added intro hook overlay (0:00-0:03)")
    
    # 0:03-0:15 - Source video segment 1 with lower-third overlay
    if len(overlay_texts['benefits']) > 0:
        benefit1_overlay = create_modern_lower_third(overlay_texts['benefits'][0])
        benefit1_clip = ImageClip(benefit1_overlay).set_duration(3.0).set_position(("center", VIDEO_HEIGHT - 150))
        overlays.append(benefit1_clip.set_start(5.0))
        logger.info(f"Added benefit 1 overlay (0:05-0:08): {overlay_texts['benefits'][0]}")
    
    # 0:15-0:27 - Source video segment 2 with lower-third overlay
    if len(overlay_texts['benefits']) > 1:
        benefit2_overlay = create_modern_lower_third(overlay_texts['benefits'][1])
        benefit2_clip = ImageClip(benefit2_overlay).set_duration(3.0).set_position(("center", VIDEO_HEIGHT - 150))
        overlays.append(benefit2_clip.set_start(17.0))
        logger.info(f"Added benefit 2 overlay (0:17-0:20): {overlay_texts['benefits'][1]}")
    
    # 0:27-0:39 - Source video segment 3 with lower-third overlay
    if len(overlay_texts['benefits']) > 2:
        benefit3_overlay = create_modern_lower_third(overlay_texts['benefits'][2])
        benefit3_clip = ImageClip(benefit3_overlay).set_duration(3.0).set_position(("center", VIDEO_HEIGHT - 150))
        overlays.append(benefit3_clip.set_start(29.0))
        logger.info(f"Added benefit 3 overlay (0:29-0:32): {overlay_texts['benefits'][2]}")
    
    # 0:39-0:45 - CTA end card
    cta_overlay = create_modern_cta_overlay(product_name, overlay_texts['cta'])
    cta_clip = ImageClip(cta_overlay).set_duration(6.0).set_position("center")
    overlays.append(cta_clip.set_start(base_video.duration - 6))
    logger.info(f"Added CTA overlay ({base_video.duration - 6:.1f}s-{base_video.duration:.1f}s)")
    
    # Composite video with overlays
    final_video = CompositeVideoClip([base_video] + overlays)
    logger.info(f"Composited video with {len(overlays)} overlays")
    final_video = final_video.without_audio()
    logger.info("Removed original source video audio; preview audio comes only from generated voiceover")
    
    # Add generated voiceover if available. Keep the video close to the
    # narration length so the preview does not continue with a silent tail.
    if audio_file and audio_file.exists():
        try:
            audio_clip = AudioFileClip(str(audio_file))
            target_video_duration = min(
                final_video.duration,
                max(MIN_PREVIEW_DURATION_SECONDS, audio_clip.duration + VOICEOVER_END_PADDING_SECONDS),
            )
            if target_video_duration < final_video.duration:
                final_video = final_video.subclip(0, target_video_duration)
            if audio_clip.duration > target_video_duration:
                audio_clip = audio_clip.subclip(0, target_video_duration)
            final_video = final_video.set_audio(audio_clip)
            logger.info(
                "Added voiceover audio: audio_duration=%.2fs video_duration=%.2fs",
                audio_clip.duration,
                final_video.duration,
            )
        except Exception as e:
            logger.warning(f"Failed to add audio: {e}")
    
    return final_video


def render_with_slides(
    request: RenderPreviewVideoRequest,
    audio_file: Optional[Path] = None
) -> VideoFileClip:
    """
    Fall back to improved slide-based rendering when no source video is available.
    Uses modern ad-style slides without storyboard labels.
    """
    logger.info("Rendering with improved fallback slides")
    clips = []
    
    # Extract product name
    product_name = extract_product_name(request)
    overlay_texts = generate_overlay_copy(request, product_name)
    
    # Intro slide with hook
    intro_image = create_modern_slide(
        title=product_name,
        subtitle=overlay_texts['hook'],
        style="hook"
    )
    intro_clip = ImageClip(intro_image).set_duration(4.0)
    clips.append(intro_clip)
    logger.info("Added intro slide")
    
    # Benefit slides (not storyboard slides)
    for i, benefit in enumerate(overlay_texts['benefits'][:3]):
        benefit_image = create_modern_slide(
            title=f"Benefit {i+1}",
            subtitle=benefit,
            style="benefit"
        )
        benefit_clip = ImageClip(benefit_image).set_duration(5.0)
        clips.append(benefit_clip)
        logger.info(f"Added benefit slide {i+1}: {benefit}")
    
    # CTA slide
    cta_image = create_modern_slide(
        title=product_name,
        subtitle=overlay_texts['cta'],
        style="cta"
    )
    cta_clip = ImageClip(cta_image).set_duration(4.0)
    clips.append(cta_clip)
    logger.info("Added CTA slide")
    
    # Concatenate all clips
    final_video = concatenate_videoclips(clips, method="compose")
    logger.info(f"Created fallback video with {len(clips)} slides, duration: {final_video.duration:.2f}s")
    
    # Add audio if available. Keep fallback slides close to the narration
    # length so the preview does not continue with a silent tail.
    if audio_file and audio_file.exists():
        try:
            audio_clip = AudioFileClip(str(audio_file))
            target_video_duration = min(
                final_video.duration,
                max(MIN_PREVIEW_DURATION_SECONDS, audio_clip.duration + VOICEOVER_END_PADDING_SECONDS),
            )
            if target_video_duration < final_video.duration:
                final_video = final_video.subclip(0, target_video_duration)
            if audio_clip.duration > target_video_duration:
                audio_clip = audio_clip.subclip(0, target_video_duration)
            final_video = final_video.set_audio(audio_clip)
            logger.info(
                "Added voiceover audio to fallback video: audio_duration=%.2fs video_duration=%.2fs",
                audio_clip.duration,
                final_video.duration,
            )
        except Exception as e:
            logger.warning(f"Failed to add audio: {e}")
    
    return final_video


def generate_voiceover(script: str, video_id: str, target_duration: float = 45.0, voice: Optional[str] = None) -> Optional[Path]:
    """
    Generate voiceover audio using IBM Watson Text-to-Speech.
    Cleans and shortens text to fit target duration if needed.
    Returns path to generated audio file or None if failed.
    
    Args:
        script: The text to convert to speech
        video_id: Unique identifier for the video
        target_duration: Target duration in seconds (default 45.0)
        voice: IBM Watson TTS voice to use (default: uses IBM_TTS_VOICE env var)
    """
    if not IBM_TTS_AVAILABLE:
        logger.warning("IBM Watson SDK not available")
        return None
    
    if not IBM_TTS_API_KEY or not IBM_TTS_URL:
        logger.warning("IBM TTS credentials not configured")
        return None
    
    # Use provided voice or fall back to environment variable
    selected_voice = voice or IBM_TTS_VOICE
    
    try:
        # Clean and prepare script for TTS
        # Remove excessive whitespace and newlines
        cleaned_script = " ".join(script.split())
        
        # Estimate speaking duration (average ~150 words per minute)
        words = cleaned_script.split()
        estimated_duration = len(words) / 150 * 60  # seconds
        
        # If script is too long, shorten it intelligently
        if estimated_duration > target_duration:
            # Calculate how many words we can fit
            max_words = int((target_duration / 60) * 150)
            
            # Try to find a good breaking point (sentence end)
            truncated_text = " ".join(words[:max_words])
            
            # Find last sentence-ending punctuation
            for punct in ['. ', '! ', '? ']:
                last_punct = truncated_text.rfind(punct)
                if last_punct > len(truncated_text) * 0.7:  # At least 70% of text
                    truncated_text = truncated_text[:last_punct + 1]
                    break
            
            cleaned_script = truncated_text
            logger.info(f"Shortened script from {len(words)} to ~{len(cleaned_script.split())} words to fit {target_duration}s")
        
        logger.info(f"Generating voiceover with voice '{selected_voice}': {len(cleaned_script)} chars, ~{len(cleaned_script.split())} words")
        
        # Initialize IBM Watson TTS
        authenticator = IAMAuthenticator(IBM_TTS_API_KEY)
        tts = TextToSpeechV1(authenticator=authenticator)
        tts.set_service_url(IBM_TTS_URL)
        
        # Synthesize speech with selected voice
        response = tts.synthesize(
            text=cleaned_script,
            voice=selected_voice,
            accept="audio/mp3"
        ).get_result()
        
        # Save audio file
        audio_filename = f"voiceover_{video_id}.mp3"
        audio_path = OUTPUT_DIR / audio_filename
        
        with open(audio_path, "wb") as audio_file:
            audio_file.write(response.content)
        
        logger.info(f"Voiceover generated successfully with voice '{selected_voice}': {audio_path}")
        return audio_path
        
    except Exception as e:
        logger.error(f"Failed to generate voiceover with voice '{selected_voice}': {e}", exc_info=True)
        return None


def extract_product_name(request: RenderPreviewVideoRequest) -> str:
    """
    Extract product name from campaign data.
    """
    # Try to extract from main_hook or video_concept
    text = request.main_hook or request.video_concept or ""
    
    # Look for common patterns
    if "LaunchBoard" in text:
        return "LaunchBoard"
    
    # Extract first capitalized word or phrase
    words = text.split()
    for word in words:
        if word and word[0].isupper() and len(word) > 3:
            return word
    
    return "Your Product"


def generate_overlay_copy(request: RenderPreviewVideoRequest, product_name: str) -> dict:
    """
    Generate product-specific overlay copy for modern SaaS ad.
    Returns dict with 'hook', 'benefits' list, and 'cta'.
    """
    # LaunchBoard-specific copy
    if "LaunchBoard" in product_name or "launch" in request.main_hook.lower():
        return {
            'hook': "Launch your MVP with confidence",
            'benefits': [
                "Plan your MVP launch in one workspace",
                "Track blockers before launch day",
                "Turn engineering progress into a launch story"
            ],
            'cta': "Move from prototype to launch-ready"
        }
    
    # Generic product copy derived from campaign data
    hook = request.main_hook[:60] if len(request.main_hook) <= 60 else request.main_hook[:57] + "..."
    
    # Extract benefits from storyboard scenes or value proposition
    benefits = []
    for scene in request.storyboard_scenes[:3]:
        # Extract short benefit from scene title or narration
        benefit = scene.scene_title[:50] if len(scene.scene_title) <= 50 else scene.scene_title[:47] + "..."
        # Remove storyboard-style prefixes
        benefit = benefit.replace("Visual:", "").replace("Narration:", "").strip()
        if benefit and len(benefit) > 10:
            benefits.append(benefit)
    
    # Fallback benefits
    if len(benefits) < 3:
        benefits.extend([
            f"Solve problems with {product_name}",
            "Built for the target audience",
            "Get started today"
        ])
    
    cta = request.call_to_action[:60] if len(request.call_to_action) <= 60 else request.call_to_action[:57] + "..."
    
    return {
        'hook': hook,
        'benefits': benefits[:3],
        'cta': cta
    }


def create_modern_hook_overlay(hook_text: str) -> np.ndarray:
    """
    Create modern intro hook overlay - short and punchy.
    Max 8-10 words, centered, semi-transparent background.
    """
    img = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0, 0))
    
    # Create semi-transparent dark background box
    box = Image.new('RGBA', (VIDEO_WIDTH - 160, 280), color=(15, 25, 40, 230))
    img.paste(box, (80, 220), box)
    
    draw = ImageDraw.Draw(img)
    
    # Load font
    hook_font = get_font(52, bold=True)
    
    # Wrap text to fit
    wrapped_lines = wrap_text_pillow(hook_text, hook_font, VIDEO_WIDTH - 220)
    y_offset = 280
    line_height = 65
    
    for line in wrapped_lines[:2]:  # Max 2 lines
        bbox = hook_font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - line_width) // 2
        draw.text((x, y_offset), line, fill=(255, 255, 255, 255), font=hook_font)
        y_offset += line_height
    
    return np.array(img)


def create_modern_lower_third(benefit_text: str) -> np.ndarray:
    """
    Create modern lower-third overlay with short benefit text.
    Semi-transparent gradient bar with white text and green accent.
    """
    img = Image.new('RGBA', (VIDEO_WIDTH, 200), color=(0, 0, 0, 0))
    
    # Create semi-transparent gradient bar
    bar = Image.new('RGBA', (VIDEO_WIDTH - 80, 90), color=(20, 35, 55, 210))
    img.paste(bar, (40, 55), bar)
    
    # Add green accent line
    accent = Image.new('RGBA', (8, 90), color=(76, 175, 80, 255))
    img.paste(accent, (40, 55), accent)
    
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    text_font = get_font(30, bold=True)
    
    # Wrap text to fit (max 2 lines)
    wrapped_lines = wrap_text_pillow(benefit_text, text_font, VIDEO_WIDTH - 180)
    y_offset = 70
    
    for line in wrapped_lines[:2]:  # Max 2 lines
        draw.text((90, y_offset), line, fill=(255, 255, 255, 255), font=text_font)
        y_offset += 38
    
    return np.array(img)


def create_modern_cta_overlay(product_name: str, cta_text: str) -> np.ndarray:
    """
    Create modern CTA end card overlay.
    Product name + tagline, clean and professional.
    """
    img = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0, 0))
    
    # Create semi-transparent background box
    box = Image.new('RGBA', (VIDEO_WIDTH - 160, 380), color=(20, 35, 55, 240))
    img.paste(box, (80, 170), box)
    
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    product_font = get_font(64, bold=True)
    cta_font = get_font(36, bold=False)
    
    # Draw product name
    product_bbox = product_font.getbbox(product_name)
    product_width = product_bbox[2] - product_bbox[0]
    product_x = (VIDEO_WIDTH - product_width) // 2
    draw.text((product_x, 230), product_name, fill=(76, 175, 80, 255), font=product_font)
    
    # Draw CTA text with wrapping
    wrapped_lines = wrap_text_pillow(cta_text, cta_font, VIDEO_WIDTH - 220)
    y_offset = 330
    line_height = 50
    
    for line in wrapped_lines[:3]:  # Max 3 lines
        bbox = cta_font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - line_width) // 2
        draw.text((x, y_offset), line, fill=(255, 255, 255, 255), font=cta_font)
        y_offset += line_height
    
    return np.array(img)


def create_intro_overlay(main_hook: str) -> np.ndarray:
    """
    Create semi-transparent intro overlay with main hook.
    """
    img = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0, 0))
    
    # Create semi-transparent background box
    box = Image.new('RGBA', (VIDEO_WIDTH - 200, 300), color=(20, 30, 50, 220))
    img.paste(box, (100, 210), box)
    
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    title_font = get_font(56, bold=True)
    content_font = get_font(36, bold=False)
    
    # Draw title
    title = "Campaign Preview"
    title_bbox = title_font.getbbox(title)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (VIDEO_WIDTH - title_width) // 2
    draw.text((title_x, 240), title, fill=(255, 255, 255, 255), font=title_font)
    
    # Draw main hook with wrapping
    wrapped_lines = wrap_text_pillow(main_hook, content_font, VIDEO_WIDTH - 250)
    y_offset = 320
    line_height = 50
    
    for line in wrapped_lines[:3]:  # Limit to 3 lines
        bbox = content_font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - line_width) // 2
        draw.text((x, y_offset), line, fill=(173, 216, 230, 255), font=content_font)
        y_offset += line_height
    
    return np.array(img)


def create_lower_third_overlay(text: str) -> np.ndarray:
    """
    Create lower-third style overlay for scene titles.
    """
    img = Image.new('RGBA', (VIDEO_WIDTH, 200), color=(0, 0, 0, 0))
    
    # Create semi-transparent background bar
    bar = Image.new('RGBA', (VIDEO_WIDTH - 100, 100), color=(30, 50, 70, 200))
    img.paste(bar, (50, 50), bar)
    
    draw = ImageDraw.Draw(img)
    
    # Load font
    font = get_font(32, bold=True)
    
    # Draw text
    wrapped_lines = wrap_text_pillow(text, font, VIDEO_WIDTH - 200)
    y_offset = 65
    
    for line in wrapped_lines[:2]:  # Limit to 2 lines
        draw.text((100, y_offset), line, fill=(255, 255, 255, 255), font=font)
        y_offset += 40
    
    return np.array(img)


def create_cta_overlay(call_to_action: str) -> np.ndarray:
    """
    Create CTA overlay for end of video.
    """
    img = Image.new('RGBA', (VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0, 0))
    
    # Create semi-transparent background box
    box = Image.new('RGBA', (VIDEO_WIDTH - 200, 350), color=(30, 50, 70, 230))
    img.paste(box, (100, 185), box)
    
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    title_font = get_font(52, bold=True)
    content_font = get_font(36, bold=False)
    
    # Draw title
    title = "Take Action"
    title_bbox = title_font.getbbox(title)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (VIDEO_WIDTH - title_width) // 2
    draw.text((title_x, 220), title, fill=(255, 255, 255, 255), font=title_font)
    
    # Draw CTA with wrapping
    wrapped_lines = wrap_text_pillow(call_to_action, content_font, VIDEO_WIDTH - 250)
    y_offset = 310
    line_height = 50
    
    for line in wrapped_lines[:3]:  # Limit to 3 lines
        bbox = content_font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - line_width) // 2
        draw.text((x, y_offset), line, fill=(144, 238, 144, 255), font=content_font)
        y_offset += line_height
    
    return np.array(img)


def get_font(size: int, bold: bool = False):
    """
    Load DejaVu Sans font with fallback to default.
    """
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
        except Exception:
            continue
    
    # Fallback to default font
    return ImageFont.load_default()


def wrap_text_pillow(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """
    Wrap text to fit within max_width pixels.
    """
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]
        
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


def create_modern_slide(title: str, subtitle: str, style: str = "default") -> np.ndarray:
    """
    Create modern ad-style slide without storyboard labels.
    Styles: 'hook', 'benefit', 'cta'
    """
    # Color schemes based on style
    if style == "hook":
        bg_color = (15, 25, 40)
        title_color = (76, 175, 80)  # Green
        subtitle_color = (255, 255, 255)
    elif style == "cta":
        bg_color = (20, 35, 55)
        title_color = (76, 175, 80)  # Green
        subtitle_color = (255, 255, 255)
    else:  # benefit
        bg_color = (25, 35, 50)
        title_color = (255, 255, 255)
        subtitle_color = (200, 220, 240)
    
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    title_font = get_font(56, bold=True)
    subtitle_font = get_font(36, bold=False)
    
    # Draw title
    title_bbox = title_font.getbbox(title)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (VIDEO_WIDTH - title_width) // 2
    draw.text((title_x, 200), title, fill=title_color, font=title_font)
    
    # Draw subtitle with wrapping
    wrapped_lines = wrap_text_pillow(subtitle, subtitle_font, VIDEO_WIDTH - 200)
    y_offset = 320
    line_height = 50
    
    for line in wrapped_lines[:4]:  # Max 4 lines
        bbox = subtitle_font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - line_width) // 2
        draw.text((x, y_offset), line, fill=subtitle_color, font=subtitle_font)
        y_offset += line_height
    
    return np.array(img)


def create_intro_slide(main_hook: str) -> np.ndarray:
    """
    Create intro slide with main hook using Pillow.
    """
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), color=(20, 30, 50))
    draw = ImageDraw.Draw(img)
    
    title_font = get_font(48, bold=True)
    content_font = get_font(32, bold=False)
    
    title = "Campaign Preview"
    title_bbox = title_font.getbbox(title)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (VIDEO_WIDTH - title_width) // 2
    draw.text((title_x, 150), title, fill=(255, 255, 255), font=title_font)
    
    wrapped_lines = wrap_text_pillow(main_hook, content_font, VIDEO_WIDTH - 150)
    y_offset = 300
    line_height = 45
    
    for line in wrapped_lines:
        bbox = content_font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - line_width) // 2
        draw.text((x, y_offset), line, fill=(173, 216, 230), font=content_font)
        y_offset += line_height
    
    return np.array(img)


def create_scene_slide(
    timestamp: str,
    scene_title: str,
    visual_direction: str,
    narration: str,
) -> np.ndarray:
    """
    Create storyboard scene slide using Pillow.
    """
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), color=(25, 35, 45))
    draw = ImageDraw.Draw(img)
    
    timestamp_font = get_font(28, bold=True)
    title_font = get_font(42, bold=True)
    label_font = get_font(24, bold=True)
    content_font = get_font(24, bold=False)
    
    draw.text((50, 50), timestamp, fill=(255, 255, 0), font=timestamp_font)
    
    wrapped_title = wrap_text_pillow(scene_title, title_font, VIDEO_WIDTH - 100)
    y_offset = 120
    for line in wrapped_title:
        bbox = title_font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - line_width) // 2
        draw.text((x, y_offset), line, fill=(255, 255, 255), font=title_font)
        y_offset += 50
    
    y_offset = max(y_offset + 30, 250)
    draw.text((100, y_offset), "Visual:", fill=(173, 216, 230), font=label_font)
    
    wrapped_visual = wrap_text_pillow(visual_direction, content_font, VIDEO_WIDTH - 200)
    y_offset += 40
    for line in wrapped_visual[:3]:
        draw.text((100, y_offset), line, fill=(211, 211, 211), font=content_font)
        y_offset += 32
    
    y_offset = max(y_offset + 30, 450)
    draw.text((100, y_offset), "Narration:", fill=(144, 238, 144), font=label_font)
    
    wrapped_narration = wrap_text_pillow(narration, content_font, VIDEO_WIDTH - 200)
    y_offset += 40
    for line in wrapped_narration[:3]:
        draw.text((100, y_offset), line, fill=(211, 211, 211), font=content_font)
        y_offset += 32
    
    return np.array(img)


def create_cta_slide(call_to_action: str) -> np.ndarray:
    """
    Create call-to-action slide using Pillow.
    """
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), color=(30, 50, 70))
    draw = ImageDraw.Draw(img)
    
    title_font = get_font(48, bold=True)
    content_font = get_font(32, bold=False)
    
    title = "Call to Action"
    title_bbox = title_font.getbbox(title)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (VIDEO_WIDTH - title_width) // 2
    draw.text((title_x, 150), title, fill=(255, 255, 255), font=title_font)
    
    wrapped_lines = wrap_text_pillow(call_to_action, content_font, VIDEO_WIDTH - 150)
    y_offset = 300
    line_height = 45
    
    for line in wrapped_lines:
        bbox = content_font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - line_width) // 2
        draw.text((x, y_offset), line, fill=(144, 238, 144), font=content_font)
        y_offset += line_height
    
    return np.array(img)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8004)


# Made with Bob
