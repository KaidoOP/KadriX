# Test KadriX Creative Service Video Generation
Write-Host "Testing Creative Service Video Generation..." -ForegroundColor Cyan

# Read the test JSON
$jsonBody = Get-Content -Path "test-video-generation.json" -Raw

# Make the API request
Write-Host "`nSending request to API Gateway..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest `
        -Uri "http://localhost:8000/api/creative/render-preview-video" `
        -Method POST `
        -Body $jsonBody `
        -ContentType "application/json" `
        -UseBasicParsing `
        -TimeoutSec 180

    Write-Host "`nSuccess! Response:" -ForegroundColor Green
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
    
    # Parse the response to get video URL
    $result = $response.Content | ConvertFrom-Json
    Write-Host "`nVideo generated successfully!" -ForegroundColor Green
    Write-Host "Campaign ID: $($result.campaign_id)" -ForegroundColor Cyan
    Write-Host "Filename: $($result.filename)" -ForegroundColor Cyan
    Write-Host "Duration: $($result.duration_seconds) seconds" -ForegroundColor Cyan
    Write-Host "Video URL: $($result.video_url)" -ForegroundColor Cyan
    Write-Host "Status: $($result.status)" -ForegroundColor Cyan
    
} catch {
    Write-Host "`nError occurred:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response body: $responseBody" -ForegroundColor Red
    }
}

# Made with Bob
