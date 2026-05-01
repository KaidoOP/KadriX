"""
KadriX Campaign Service
Generates marketing campaigns based on product ideas
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

app = FastAPI(title="KadriX Campaign Service", version="1.0.0")

# Request/Response Models
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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "campaign-service",
        "version": "1.0.0"
    }

@app.post("/campaigns/generate", response_model=CampaignResponse)
async def generate_campaign(request: CampaignGenerateRequest):
    """
    Generate a marketing campaign based on product idea
    Returns mock data for hackathon demo
    """
    campaign_id = str(uuid.uuid4())
    
    # Generate mock campaign data
    campaign = CampaignResponse(
        campaign_id=campaign_id,
        version=1,
        generated_at=datetime.utcnow().isoformat(),
        product_summary=f"Innovative solution: {request.product_idea}. {request.description[:100]}",
        target_audience=request.target_audience,
        campaign_angle=f"Emphasizing {request.campaign_goal} with a {request.tone} approach",
        value_proposition=f"Transform your experience with {request.product_idea} - the smart choice for {request.target_audience}",
        marketing_hooks=[
            f"Revolutionary {request.product_idea} that changes everything",
            f"Perfect for {request.target_audience} who want results",
            f"Achieve {request.campaign_goal} faster than ever before",
            "Join thousands of satisfied customers today"
        ],
        ad_copy_variants=[
            AdCopyVariant(
                platform="Facebook",
                headline=f"Discover {request.product_idea}",
                body=f"Are you ready to {request.campaign_goal}? Our {request.product_idea} is designed specifically for {request.target_audience}. {request.description[:80]}... Learn more!",
                character_count=180
            ),
            AdCopyVariant(
                platform="Instagram",
                headline=f"✨ {request.product_idea}",
                body=f"Transform your life! Perfect for {request.target_audience}. {request.description[:60]}... 🚀 #Innovation #Success",
                character_count=150
            ),
            AdCopyVariant(
                platform="LinkedIn",
                headline=f"Professional Solution: {request.product_idea}",
                body=f"Attention {request.target_audience}: Achieve {request.campaign_goal} with our proven solution. {request.description[:100]}... Connect with us to learn more.",
                character_count=220
            )
        ],
        call_to_action=f"Start your journey with {request.product_idea} today - Limited time offer!",
        video_script=f"""
[OPENING SHOT]
Visual: {request.video_context or 'Product showcase'}

[HOOK - 0:00-0:03]
"Are you struggling with {request.campaign_goal}?"

[PROBLEM - 0:03-0:08]
"Most {request.target_audience} face challenges that hold them back."

[SOLUTION - 0:08-0:15]
"Introducing {request.product_idea} - {request.description[:80]}"

[BENEFITS - 0:15-0:25]
"With our {request.tone} approach, you'll achieve:
- Faster results
- Better outcomes
- Peace of mind"

[SOCIAL PROOF - 0:25-0:30]
"Join thousands who have already transformed their experience."

[CALL TO ACTION - 0:30-0:35]
"Visit our website today and start your journey. Limited time offer!"

[CLOSING]
Visual: Logo and website URL
"""
    )
    
    return campaign

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

# Made with Bob
