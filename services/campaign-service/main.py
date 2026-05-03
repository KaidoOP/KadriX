"""
KadriX Campaign Service
Generates campaign blueprints from product ideas and demo-video context.
"""
from datetime import datetime
import json
import logging
import os
from typing import List, Optional
import uuid

from fastapi import FastAPI
from pydantic import BaseModel

try:
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    WATSONX_AVAILABLE = True
except ImportError:
    WATSONX_AVAILABLE = False

app = FastAPI(title="KadriX Campaign Service", version="1.1.0")
logger = logging.getLogger(__name__)

USE_WATSONX = os.getenv("USE_WATSONX", "false").lower() == "true"
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
WATSONX_MODEL_ID = os.getenv("WATSONX_MODEL_ID", "ibm/granite-4-h-small")


class CampaignGenerateRequest(BaseModel):
    product_idea: str
    description: str
    campaign_goal: str
    target_audience: str
    tone: str
    video_context: Optional[str] = None


class AdCopyVariant(BaseModel):
    platform: str
    headline: str
    body: str
    character_count: int


class StoryboardScene(BaseModel):
    timestamp: str
    scene_title: str
    visual_direction: str
    narration: str


class CampaignResponse(BaseModel):
    campaign_id: str
    version: int
    generated_at: str
    product_summary: str
    target_audience: str
    campaign_angle: str
    value_proposition: str
    marketing_hooks: List[str]
    ad_copy_variants: List[AdCopyVariant]
    call_to_action: str
    video_script: str
    main_hook: str
    voiceover_script: str
    video_concept: str
    storyboard_scenes: List[StoryboardScene]
    mood_direction: str
    music_direction: str
    visual_style: str
    one_minute_video_plan: str
    generation_source: str = "template"
    model_id: Optional[str] = None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "campaign-service",
        "version": "1.1.0",
        "watsonx_enabled": is_watsonx_configured(),
        "watsonx_model_id": WATSONX_MODEL_ID if is_watsonx_configured() else None,
    }


@app.post("/campaigns/generate", response_model=CampaignResponse)
async def generate_campaign(request: CampaignGenerateRequest):
    """
    Generate a product-specific launch campaign and 60-second video ad blueprint.

    Uses IBM watsonx.ai when configured and falls back to deterministic MVP logic.
    """
    campaign_id = str(uuid.uuid4())
    generated_at = datetime.utcnow().isoformat()

    if is_watsonx_configured():
        try:
            blueprint = build_campaign_blueprint_with_watsonx(request)
            return CampaignResponse(
                campaign_id=campaign_id,
                version=1,
                generated_at=generated_at,
                generation_source="watsonx.ai",
                model_id=WATSONX_MODEL_ID,
                **blueprint,
            )
        except Exception as exc:
            logger.warning("watsonx campaign generation failed; using template fallback: %s", exc)

    return CampaignResponse(
        campaign_id=campaign_id,
        version=1,
        generated_at=generated_at,
        generation_source="template_fallback",
        **build_campaign_blueprint(request),
    )


def is_watsonx_configured() -> bool:
    return bool(USE_WATSONX and WATSONX_AVAILABLE and WATSONX_API_KEY and WATSONX_PROJECT_ID)


def build_campaign_blueprint_with_watsonx(request: CampaignGenerateRequest) -> dict:
    model = ModelInference(
        model_id=WATSONX_MODEL_ID,
        credentials=Credentials(api_key=WATSONX_API_KEY, url=WATSONX_URL),
        project_id=WATSONX_PROJECT_ID,
        params={
            "decoding_method": "sample",
            "temperature": 0.55,
            "top_p": 0.85,
            "max_new_tokens": 1800,
            "min_new_tokens": 500,
        },
    )
    generated_text = model.generate_text(prompt=build_watsonx_campaign_prompt(request))
    data = parse_json_object(generated_text)
    fallback = build_campaign_blueprint(request)

    for key, value in fallback.items():
        data.setdefault(key, value)

    data["ad_copy_variants"] = [
        build_ad_variant(
            platform=item.get("platform", "LinkedIn"),
            headline=item.get("headline", "")[:90],
            body=item.get("body", "")[:600],
        )
        for item in data.get("ad_copy_variants", [])
        if isinstance(item, dict)
    ] or fallback["ad_copy_variants"]

    data["storyboard_scenes"] = [
        StoryboardScene(
            timestamp=item.get("timestamp", ""),
            scene_title=item.get("scene_title", ""),
            visual_direction=item.get("visual_direction", ""),
            narration=item.get("narration", ""),
        )
        for item in data.get("storyboard_scenes", [])
        if isinstance(item, dict)
    ] or fallback["storyboard_scenes"]

    return data


def build_watsonx_campaign_prompt(request: CampaignGenerateRequest) -> str:
    return f"""
You are KadriX, an IBM hackathon launch strategist for developer products.
Generate one launch campaign blueprint as strict JSON only. No markdown. No explanation.

Product idea: {request.product_idea}
Description: {request.description}
Campaign goal: {request.campaign_goal}
Target audience: {request.target_audience}
Tone: {request.tone}
Demo/video context: {request.video_context or "No uploaded video context provided."}

Required JSON keys:
product_summary: string
target_audience: string
campaign_angle: string
value_proposition: string
marketing_hooks: array of 4 concise strings
ad_copy_variants: array of 3 objects with platform, headline, body
call_to_action: string
video_script: string
main_hook: string
voiceover_script: string
video_concept: string
storyboard_scenes: array of 6 objects with timestamp, scene_title, visual_direction, narration
mood_direction: string
music_direction: string
visual_style: string
one_minute_video_plan: string

Make it specific to the product, demo-led, credible for a hackathon MVP, and suitable for a 60-second launch preview video.
"""


def parse_json_object(raw_text: str) -> dict:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json\n", "", 1).replace("JSON\n", "", 1)

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("watsonx response did not contain a JSON object")

    parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("watsonx response JSON was not an object")
    return parsed


def build_campaign_blueprint(request: CampaignGenerateRequest) -> dict:
    tone_profile = get_tone_profile(request.tone)
    product = clean_text(request.product_idea)
    description = clean_text(request.description)
    goal = clean_text(request.campaign_goal)
    audience = clean_text(request.target_audience)
    video_context = clean_text(request.video_context or "")
    has_video_context = bool(video_context)

    product_focus = extract_focus_phrase(description)
    product_focus_inline = lower_first(product_focus)
    walkthrough_focus = build_walkthrough_focus(video_context)
    goal_inline = lower_first(goal)
    context_sentence = (
        f"Based on the uploaded product walkthrough, the campaign should focus on {walkthrough_focus}."
        if has_video_context
        else f"The campaign should show {product} in a practical product workflow, not as an abstract claim."
    )

    main_hook = build_main_hook(
        product=product,
        audience=audience,
        product_focus=product_focus_inline,
        has_video_context=has_video_context,
    )
    value_proposition = (
        f"{product} helps {audience} understand the product value faster by turning "
        f"{product_focus_inline} into a clear, visible workflow."
    )
    storyboard_scenes = build_storyboard_scenes(
        product=product,
        audience=audience,
        goal=goal,
        product_focus=product_focus_inline,
        context_sentence=context_sentence,
        tone_profile=tone_profile,
        has_video_context=has_video_context,
    )
    voiceover_script = build_voiceover_script(
        product=product,
        audience=audience,
        goal=goal,
        product_focus=product_focus_inline,
        context_sentence=context_sentence,
        tone_profile=tone_profile,
    )

    ad_copy_variants = [
        build_ad_variant(
            platform="LinkedIn",
            headline=f"See {product} in action",
            body=(
                f"For {audience}, {product} becomes easier to trust when the workflow is visible. "
                f"This campaign uses the demo to connect {product_focus_inline} with the launch goal: {goal_inline}."
            ),
        ),
        build_ad_variant(
            platform="Instagram",
            headline="From demo to decision",
            body=(
                f"Show the product, not just the promise. A short walkthrough makes {product} clear "
                f"for {audience} and highlights why {product_focus_inline} matters."
            ),
        ),
        build_ad_variant(
            platform="YouTube Shorts",
            headline=f"{product} in 60 seconds",
            body=(
                f"A compact demo-led ad: problem, product walkthrough, result moment, and a direct "
                f"next step tied to the launch goal."
            ),
        ),
    ]

    return {
        "product_summary": (
            f"{product} is positioned as a practical solution for {audience}. "
            f"The campaign should explain the product through its real workflow: {product_focus_inline}. "
            f"{context_sentence}"
        ),
        "target_audience": audience,
        "campaign_angle": (
            f"Use a walkthrough-led launch angle: start with the user problem, move into the "
            f"{product} demo, then show the moment the benefit becomes obvious. {context_sentence}"
        ),
        "value_proposition": value_proposition,
        "marketing_hooks": [
            main_hook,
            f"Show {audience} the exact moment {product} becomes useful.",
            f"Turn the demo into proof: {product_focus_inline}.",
            f"Make the launch goal concrete with a product walkthrough: {goal_inline}.",
        ],
        "ad_copy_variants": ad_copy_variants,
        "call_to_action": f"Watch the walkthrough and see how {product} supports the goal: {goal_inline}.",
        "video_script": build_legacy_video_script(storyboard_scenes),
        "main_hook": main_hook,
        "voiceover_script": voiceover_script,
        "video_concept": (
            f"A 60-second product-demo ad that starts with the user's current friction, cuts into "
            f"the {product} walkthrough, highlights {product_focus_inline}, and ends with a direct action "
            f"linked to {goal}."
        ),
        "storyboard_scenes": storyboard_scenes,
        "mood_direction": tone_profile["mood"],
        "music_direction": tone_profile["music"],
        "visual_style": tone_profile["visual_style"],
        "one_minute_video_plan": (
            "0-5s hook, 5-15s problem context, 15-35s product walkthrough, 35-48s outcome proof, "
            "48-56s campaign promise, 56-60s call to action. When video_context is available, use "
            "the uploaded walkthrough as the main visual source for the middle section."
        ),
    }


def get_tone_profile(tone: str) -> dict:
    normalized = tone.strip().lower()
    profiles = {
        "professional": {
            "voiceover_style": "measured, credible, and direct",
            "mood": "Clear, confident, and trustworthy with a focus on practical outcomes.",
            "music": "Modern corporate pulse, light percussion, steady tempo, no dramatic drops.",
            "visual_style": "Clean dashboard close-ups, calm transitions, readable captions, product-first framing.",
        },
        "humorous": {
            "voiceover_style": "warm, quick, and lightly comedic",
            "mood": "Playful, fast-moving, and approachable without making the product feel unserious.",
            "music": "Upbeat indie pop rhythm with light percussion and small comedic pauses.",
            "visual_style": "Quick before-and-after cuts, expressive captions, simple visual contrast.",
        },
        "premium": {
            "voiceover_style": "calm, precise, and polished",
            "mood": "Minimal, elegant, calm, and high-trust.",
            "music": "Sparse ambient bed with soft piano or muted electronic texture.",
            "visual_style": "Slow product close-ups, generous spacing, dark neutral backgrounds, minimal overlays.",
        },
        "emotional": {
            "voiceover_style": "empathetic, grounded, and personal",
            "mood": "Warm, story-driven, human-centered, and focused on relief or progress.",
            "music": "Soft cinematic build with gentle piano and light strings.",
            "visual_style": "Human workflow moments, soft lighting, slower pacing, outcome-focused scenes.",
        },
        "technical": {
            "voiceover_style": "specific, structured, and evidence-oriented",
            "mood": "Precise, feature-led, credible, and practical.",
            "music": "Minimal electronic pulse with clean beats and subtle data-product energy.",
            "visual_style": "Interface close-ups, annotations, feature callouts, metric overlays, sharp cuts.",
        },
    }
    return profiles.get(normalized, profiles["professional"])


def clean_text(value: str) -> str:
    return " ".join(value.split()).strip()


def extract_focus_phrase(description: str) -> str:
    if not description:
        return "the core product workflow"
    sentence = description.split(".")[0].strip()
    return sentence[:180].rstrip(",;:")


def build_walkthrough_focus(video_context: str) -> str:
    if not video_context:
        return ""
    words = video_context.split()
    compact_context = " ".join(words[:34])
    cleaned = compact_context.rstrip(",.;:").lower()
    prefixes = [
        "uploaded walkthrough shows ",
        "the uploaded walkthrough shows ",
        "walkthrough shows ",
        "video shows ",
        "the video shows ",
    ]
    for prefix in prefixes:
        if cleaned.startswith(prefix):
            return cleaned[len(prefix):]
    return cleaned


def lower_first(value: str) -> str:
    if not value:
        return value
    return value[0].lower() + value[1:]


def build_main_hook(product: str, audience: str, product_focus: str, has_video_context: bool) -> str:
    if has_video_context:
        return (
            f"See how {product} works in the actual walkthrough, from first interaction to the "
            f"moment {audience} can understand the value."
        )
    return f"Show {audience} how {product} delivers {product_focus} in under one minute."


def build_ad_variant(platform: str, headline: str, body: str) -> AdCopyVariant:
    return AdCopyVariant(
        platform=platform,
        headline=headline,
        body=body,
        character_count=len(f"{headline} {body}"),
    )


def build_voiceover_script(
    product: str,
    audience: str,
    goal: str,
    product_focus: str,
    context_sentence: str,
    tone_profile: dict,
) -> str:
    return (
        f"Voiceover style: {tone_profile['voiceover_style']}. "
        f"For {audience}, a product becomes convincing when the workflow is easy to see. "
        f"This is {product}: built around {product_focus}. {context_sentence} "
        f"First, show the everyday friction. Then move into the walkthrough: setup, key interaction, "
        f"dashboard or result, and the clearest outcome. Close by connecting that outcome to "
        f"the goal: {lower_first(goal)}. Then invite viewers to watch the full demo."
    )


def build_storyboard_scenes(
    product: str,
    audience: str,
    goal: str,
    product_focus: str,
    context_sentence: str,
    tone_profile: dict,
    has_video_context: bool,
) -> List[StoryboardScene]:
    source_visual = "uploaded walkthrough footage" if has_video_context else "product UI or demo footage"
    return [
        StoryboardScene(
            timestamp="0:00-0:05",
            scene_title="Immediate Hook",
            visual_direction=(
                f"Open on the strongest frame from the {source_visual}; add one concise on-screen claim."
            ),
            narration=f"For {audience}, the value of {product} should be visible in seconds.",
        ),
        StoryboardScene(
            timestamp="0:05-0:15",
            scene_title="Problem Context",
            visual_direction=f"Show the manual step, delay, or uncertainty that {product} removes.",
            narration=f"The campaign starts with the friction behind the launch goal: {lower_first(goal)}.",
        ),
        StoryboardScene(
            timestamp="0:15-0:35",
            scene_title="Product Walkthrough",
            visual_direction=(
                f"Use the demo sequence to show {product_focus}; crop tightly around key interactions."
            ),
            narration=context_sentence,
        ),
        StoryboardScene(
            timestamp="0:35-0:48",
            scene_title="Outcome Reveal",
            visual_direction="Show the dashboard, result screen, completed workflow, or visible before-and-after moment.",
            narration=(
                f"Make the outcome concrete so {audience} can understand what improves after using {product}."
            ),
        ),
        StoryboardScene(
            timestamp="0:48-0:56",
            scene_title="Campaign Promise",
            visual_direction=(
                f"Pair the clearest product benefit with the tone direction: {tone_profile['mood']}"
            ),
            narration=f"{product} turns the product demo into a believable reason to act.",
        ),
        StoryboardScene(
            timestamp="0:56-1:00",
            scene_title="Call to Action",
            visual_direction="End on the product name, short CTA, and clean URL or next-step card.",
            narration=f"Watch the full walkthrough and see how {product} supports the goal: {lower_first(goal)}.",
        ),
    ]


def build_legacy_video_script(storyboard_scenes: List[StoryboardScene]) -> str:
    sections = []
    for scene in storyboard_scenes:
        sections.append(
            f"[{scene.timestamp} - {scene.scene_title}]\n"
            f"Visual: {scene.visual_direction}\n"
            f"Narration: {scene.narration}"
        )
    return "\n\n".join(sections)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)


# Made with Bob
