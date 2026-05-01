"""
KadriX Feedback Service
Improves campaigns based on user feedback
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

app = FastAPI(title="KadriX Feedback Service", version="1.0.0")

# Request/Response Models
class FeedbackImproveRequest(BaseModel):
    campaign_id: str
    original_campaign: Dict[str, Any]
    feedback: str

class ImprovedCampaign(BaseModel):
    campaign_id: str
    version: int
    generated_at: str
    original: Dict[str, Any]
    improved: Dict[str, Any]
    changes: List[str]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "feedback-service",
        "version": "1.0.0"
    }

@app.post("/feedback/improve", response_model=ImprovedCampaign)
async def improve_campaign(request: FeedbackImproveRequest):
    """
    Improve campaign based on user feedback
    Returns mock improved campaign for hackathon demo
    """
    # Extract original campaign data
    original = request.original_campaign
    
    # Create improved version based on feedback
    # In production, this would use IBM watsonx.ai for intelligent improvements
    improved = original.copy()
    changes = []
    
    # Analyze feedback and make improvements
    feedback_lower = request.feedback.lower()
    
    # Adjust tone based on feedback
    if "more professional" in feedback_lower or "formal" in feedback_lower:
        improved["tone"] = "professional and authoritative"
        improved["value_proposition"] = f"Enterprise-grade solution: {original.get('product_summary', 'Our product')} delivers measurable ROI"
        changes.append("Adjusted tone to be more professional and formal")
        changes.append("Enhanced value proposition with business-focused language")
    
    if "casual" in feedback_lower or "friendly" in feedback_lower:
        improved["tone"] = "casual and approachable"
        improved["value_proposition"] = f"Hey! Check out {original.get('product_summary', 'our awesome product')} - it's a game-changer!"
        changes.append("Made tone more casual and friendly")
        changes.append("Simplified value proposition for broader appeal")
    
    # Adjust target audience based on feedback
    if "younger" in feedback_lower or "millennials" in feedback_lower or "gen z" in feedback_lower:
        improved["target_audience"] = "Millennials and Gen Z (ages 18-35)"
        improved["marketing_hooks"] = [
            "🔥 The future is here - don't get left behind",
            "Join the movement - thousands already have",
            "Your friends are already using it. What are you waiting for?",
            "Sustainable, smart, and totally worth it"
        ]
        changes.append("Refocused target audience to younger demographics")
        changes.append("Updated marketing hooks with trending language and emojis")
    
    if "older" in feedback_lower or "mature" in feedback_lower or "senior" in feedback_lower:
        improved["target_audience"] = "Mature professionals and retirees (ages 50+)"
        improved["marketing_hooks"] = [
            "Trusted by thousands of satisfied customers",
            "Simple, reliable, and backed by our guarantee",
            "Experience matters - that's why we built this for you",
            "Quality you can depend on, service you can trust"
        ]
        changes.append("Adjusted target audience to mature demographics")
        changes.append("Refined marketing hooks to emphasize trust and reliability")
    
    # Adjust campaign goal based on feedback
    if "awareness" in feedback_lower or "brand" in feedback_lower:
        improved["campaign_angle"] = "Building brand awareness and market presence"
        improved["call_to_action"] = "Learn more about our story and vision"
        changes.append("Shifted focus to brand awareness")
        changes.append("Updated call-to-action for educational engagement")
    
    if "conversion" in feedback_lower or "sales" in feedback_lower or "buy" in feedback_lower:
        improved["campaign_angle"] = "Driving immediate conversions and sales"
        improved["call_to_action"] = "Buy now and save 20% - Limited time offer!"
        changes.append("Optimized for conversion and sales")
        changes.append("Added urgency to call-to-action with discount offer")
    
    # Add more hooks if feedback mentions "more examples" or "more options"
    if "more" in feedback_lower and ("example" in feedback_lower or "option" in feedback_lower or "hook" in feedback_lower):
        if "marketing_hooks" in improved:
            improved["marketing_hooks"].extend([
                "See why industry leaders choose us",
                "Transform your results in just days",
                "Risk-free trial - no credit card required"
            ])
            changes.append("Added additional marketing hooks for variety")
    
    # If no specific changes were made, provide general improvements
    if not changes:
        improved["value_proposition"] = f"Enhanced: {original.get('value_proposition', 'Our solution')} - now with improved clarity and impact"
        improved["campaign_angle"] = f"Refined approach: {original.get('campaign_angle', 'Strategic positioning')} with stronger messaging"
        changes.append("Applied general improvements to value proposition")
        changes.append("Refined campaign angle for better clarity")
        changes.append("Optimized messaging based on best practices")
    
    # Create response
    response = ImprovedCampaign(
        campaign_id=request.campaign_id,
        version=2,
        generated_at=datetime.utcnow().isoformat(),
        original=original,
        improved=improved,
        changes=changes
    )
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

# Made with Bob
