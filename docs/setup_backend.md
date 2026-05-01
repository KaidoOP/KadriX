# KadriX Backend Setup Guide

This guide explains how to set up and run the KadriX backend microservices locally using Docker.

## Architecture Overview

KadriX uses a microservice architecture with the following services:

- **API Gateway** (port 8000) - Main entry point for all client requests
- **Campaign Service** (port 8001) - Generates marketing campaigns
- **Media Service** (port 8002) - Handles video uploads and analysis
- **Feedback Service** (port 8003) - Improves campaigns based on feedback

All services communicate via HTTP using Docker service names.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose (included with Docker Desktop)
- Git (to clone the repository)
- curl or Postman (for testing)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd KadriX
```

### 2. Start All Services

```bash
docker compose up --build
```

This command will:
- Build Docker images for all services
- Start all containers
- Set up networking between services
- Expose ports on your local machine

**Note:** The first build may take a few minutes as it downloads base images and installs dependencies.

### 3. Verify Services are Running

Check that all services are healthy:

```bash
# API Gateway
curl http://localhost:8000/health

# Campaign Service
curl http://localhost:8001/health

# Media Service
curl http://localhost:8002/health

# Feedback Service
curl http://localhost:8003/health
```

Each should return a JSON response with `"status": "healthy"`.

## Testing the API

### Generate a Campaign

```bash
curl -X POST http://localhost:8000/api/campaigns/generate \
  -H "Content-Type: application/json" \
  -d '{
    "product_idea": "Smart Home Assistant",
    "description": "AI-powered device that helps manage your home",
    "campaign_goal": "increase brand awareness",
    "target_audience": "tech-savvy homeowners",
    "tone": "friendly and innovative"
  }'
```

### Upload a Video

```bash
curl -X POST http://localhost:8000/api/media/upload \
  -F "file=@/path/to/your/video.mp4"
```

### Improve a Campaign

```bash
curl -X POST http://localhost:8000/api/campaigns/improve \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "your-campaign-id",
    "original_campaign": {
      "product_summary": "Smart Home Assistant",
      "value_proposition": "Transform your home"
    },
    "feedback": "Make it more professional and formal"
  }'
```

## Service Details

### API Gateway (Port 8000)

**Endpoints:**
- `GET /health` - Health check
- `POST /api/campaigns/generate` - Generate new campaign
- `POST /api/campaigns/improve` - Improve existing campaign
- `POST /api/media/upload` - Upload video file

**Environment Variables:**
- `CAMPAIGN_SERVICE_URL` - URL of campaign service (default: http://campaign-service:8001)
- `MEDIA_SERVICE_URL` - URL of media service (default: http://media-service:8002)
- `FEEDBACK_SERVICE_URL` - URL of feedback service (default: http://feedback-service:8003)

### Campaign Service (Port 8001)

**Endpoints:**
- `GET /health` - Health check
- `POST /campaigns/generate` - Generate campaign from product idea

**Request Body:**
```json
{
  "product_idea": "string",
  "description": "string",
  "campaign_goal": "string",
  "target_audience": "string",
  "tone": "string",
  "video_context": "string (optional)"
}
```

**Response:**
```json
{
  "campaign_id": "uuid",
  "version": 1,
  "generated_at": "ISO timestamp",
  "product_summary": "string",
  "target_audience": "string",
  "campaign_angle": "string",
  "value_proposition": "string",
  "marketing_hooks": ["string"],
  "ad_copy_variants": [
    {
      "platform": "string",
      "headline": "string",
      "body": "string",
      "character_count": 0
    }
  ],
  "call_to_action": "string",
  "video_script": "string"
}
```

### Media Service (Port 8002)

**Endpoints:**
- `GET /health` - Health check
- `POST /media/upload` - Upload and analyze video

**Request:** Multipart form data with video file

**Response:**
```json
{
  "file_id": "uuid",
  "filename": "string",
  "size_bytes": 0,
  "format": "string",
  "transcript": "string",
  "product_context": "string"
}
```

### Feedback Service (Port 8003)

**Endpoints:**
- `GET /health` - Health check
- `POST /feedback/improve` - Improve campaign based on feedback

**Request Body:**
```json
{
  "campaign_id": "string",
  "original_campaign": {},
  "feedback": "string"
}
```

**Response:**
```json
{
  "campaign_id": "string",
  "version": 2,
  "generated_at": "ISO timestamp",
  "original": {},
  "improved": {},
  "changes": ["string"]
}
```

## Docker Commands

### Start services in background
```bash
docker compose up -d
```

### Stop all services
```bash
docker compose down
```

### View logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api-gateway
docker compose logs -f campaign-service
docker compose logs -f media-service
docker compose logs -f feedback-service
```

### Rebuild after code changes
```bash
docker compose up --build
```

### Remove all containers and volumes
```bash
docker compose down -v
```

## Troubleshooting

### Services won't start

1. Check Docker Desktop is running
2. Ensure ports 8000-8003 are not in use:
   ```bash
   # Windows PowerShell
   netstat -ano | findstr :8000
   netstat -ano | findstr :8001
   netstat -ano | findstr :8002
   netstat -ano | findstr :8003
   ```
3. Check logs for errors:
   ```bash
   docker compose logs
   ```

### Health checks failing

Wait 10-30 seconds after starting services for health checks to pass. Services need time to initialize.

### Connection refused errors

Ensure all services are running:
```bash
docker compose ps
```

All services should show status "Up" or "Up (healthy)".

### Port conflicts

If ports are already in use, you can modify the port mappings in `docker-compose.yml`:
```yaml
ports:
  - "9000:8000"  # Change host port (left side) only
```

## Development Workflow

1. Make code changes in service directories
2. Rebuild and restart:
   ```bash
   docker compose up --build
   ```
3. Test changes using curl or Postman
4. View logs to debug issues

## API Documentation

Once services are running, access interactive API documentation:

- API Gateway: http://localhost:8000/docs
- Campaign Service: http://localhost:8001/docs
- Media Service: http://localhost:8002/docs
- Feedback Service: http://localhost:8003/docs

## Next Steps

- Integrate IBM watsonx.ai for intelligent campaign generation
- Add IBM Watson Speech-to-Text for video transcription
- Implement frontend with Quasar + Vue 3
- Add authentication and authorization
- Implement database persistence
- Add monitoring and logging

## Support

For issues or questions:
1. Check the logs: `docker compose logs -f`
2. Review this documentation
3. Check the main README.md
4. Review architecture-plan.md in the docs/ directory