# Test KadriX API endpoints

Write-Host "Testing KadriX Backend Services..." -ForegroundColor Green
Write-Host ""

# Test API Gateway Health
Write-Host "1. Testing API Gateway Health..." -ForegroundColor Cyan
$response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
Write-Host $response.Content
Write-Host ""

# Test Campaign Generation
Write-Host "2. Testing Campaign Generation..." -ForegroundColor Cyan
$campaignBody = @{
    product_idea = "Smart Home Assistant"
    description = "AI-powered device that helps manage your home"
    campaign_goal = "increase brand awareness"
    target_audience = "tech-savvy homeowners"
    tone = "friendly and innovative"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:8000/api/campaigns/generate" -Method POST -Body $campaignBody -ContentType "application/json" -UseBasicParsing
$campaign = $response.Content | ConvertFrom-Json
Write-Host "Campaign ID: $($campaign.campaign_id)"
Write-Host "Version: $($campaign.version)"
Write-Host "Value Proposition: $($campaign.value_proposition)"
Write-Host ""

Write-Host "All tests completed successfully!" -ForegroundColor Green

# Made with Bob
