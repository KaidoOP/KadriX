# KadriX

KadriX is a developer-focused launch workflow platform that helps developers, indie hackers, hackathon teams, and startup builders turn MVP demos or technical walkthroughs into launch-ready product messaging, video ad blueprints, storyboards, and preview assets faster.

The project is built for the **IBM Bob Dev Day Hackathon** under the challenge theme:

> Turn idea into impact faster

KadriX bridges the gap between "we built something" and "we know how to talk about it" — without needing a full creative agency workflow.

---

## What KadriX Does

KadriX provides a developer launch workflow dashboard for transforming technical demos into launch-ready marketing assets.

A developer can submit:

- MVP demo or technical walkthrough
- Short product description
- Campaign goal
- Target audience
- Desired tone of voice
- Optional demo-video context or transcript

KadriX then generates a launch package containing:

- Product summary
- Target audience
- Campaign angle
- Key value proposition
- Marketing hooks
- Ad copy variants
- Call to action
- Short video ad script
- Improved campaign version based on user feedback

---

## Problem

Many developers, indie hackers, and hackathon teams already have a working MVP, prototype, or technical demo. The harder part starts when they need to turn that technical achievement into clear product messaging for launch.

They still need to answer questions such as:

- What is the product really about (beyond the tech)?
- Who is the ideal audience?
- What is the strongest value proposition?
- Which campaign angle should be used?
- Which hooks and ad copies fit the product?
- How should the message change after feedback?

For developer teams, this process is often slow, unfamiliar, and expensive.

---

## Solution

KadriX turns technical demos into structured launch-ready output through a simple feedback-driven workflow.

```text
MVP demo or technical walkthrough
  -> product and audience understanding
  -> campaign generation
  -> campaign preview
  -> developer feedback
  -> improved campaign version
```

The goal is to help developers move from working demo to usable launch messaging faster.

---

## MVP Scope

The hackathon MVP focuses on a stable and demonstrable proof of concept.

### Included

- Campaign workflow dashboard with structured workspace
- Product brief input
- Optional demo-video upload flow
- Mock transcript or sample video context
- Campaign generation
- Campaign preview
- Feedback loop
- Improved campaign version
- Preview video generation (under validation)
- Microservice-oriented backend structure
- IBM Bob session reports in `/bob_sessions`

### Not Included

- Real ad publishing
- Full analytics dashboard
- Production-grade video editing
- User authentication
- Billing
- Kubernetes deployment
- IBM watsonx.ai integration (planned future enhancement)
- IBM Speech-to-Text integration (planned future enhancement)
- IBM Text-to-Speech integration (planned future enhancement)

---

## IBM Bob Usage

KadriX was built using **IBM Bob IDE** as the primary documented development partner for this project.

IBM Bob IDE was used interactively throughout development for:

- Planning the MVP scope
- Designing the microservice-oriented architecture
- Creating backend services
- Building the frontend structure
- Implementing campaign generation logic
- Implementing the feedback loop
- Technical review and debugging
- Creative-service planning and implementation
- Improving code quality
- Writing documentation
- Preparing the hackathon submission

**Important:** IBM Bob was used through the **Bob IDE** as an interactive development partner, not called programmatically through an API. Bob helped accelerate development by providing architecture guidance, code generation, and technical review throughout the project lifecycle.

Relevant exported IBM Bob task session reports and consumption summary screenshots are stored in:

```text
bob_sessions/
```

---

## Planned IBM Service Integrations

KadriX is designed to support optional IBM service integrations as future enhancements:

### IBM watsonx.ai (Planned)

Possible use cases:
- Generate campaign strategy
- Support hook and ad copy creation
- Support short video script creation
- Improve campaign output based on feedback
- Rewrite content for different tones

**Status:** Not yet implemented. The MVP uses template-based generation.

### IBM Speech-to-Text (Planned)

Possible use cases:
- Transcribe uploaded demo videos automatically
- Extract product context from video narration
- Support multiple languages

**Status:** Not yet implemented. The MVP uses mock transcripts or sample video context.

### IBM Text-to-Speech (Planned)

Possible use cases:
- Generate voiceover for preview videos
- Support multiple voices and languages
- Enhance video preview quality

**Status:** Not yet implemented. Preview videos currently use text slides only.

---

## Architecture

KadriX is structured as a microservice-oriented monorepo.

```text
KadriX/
  frontend/
  services/
    api-gateway/
    campaign-service/
    media-service/
    feedback-service/
  shared/
  docs/
  demo/
  bob_sessions/
  README.md
```

---

## Services

### Frontend

The frontend provides the user-facing campaign workflow dashboard.

Responsibilities:

- Campaign workflow dashboard with structured workspace
- Product brief form
- Demo-video upload UI
- Campaign preview with expandable sections
- Feedback input with quick suggestions
- Version comparison with side-by-side layout

Technology:

- Quasar Framework 2.x
- Vue 3
- TypeScript
- Vite

### API Gateway

The API Gateway is the central entry point for the frontend.

Responsibilities:

- Receive frontend requests
- Route requests to internal services
- Expose a clean public API
- Handle CORS
- Normalize responses

Technology:

- Python
- FastAPI

Planned endpoints:

```text
GET  /health
POST /api/campaigns/generate
POST /api/campaigns/improve
POST /api/media/upload
```

### Campaign Service

The Campaign Service creates the first campaign version.

Responsibilities:

- Process product brief or transcript context
- Generate product summary
- Generate campaign angle
- Generate hooks
- Generate ad copy variants
- Generate CTA
- Generate short video ad script

Technology:

- Python
- FastAPI

Planned endpoints:

```text
GET  /health
POST /campaigns/generate
```

### Media Service

The Media Service handles demo-video input.

Responsibilities:

- Accept uploaded video files
- Store basic metadata
- Return mock transcript or sample video context
- Prepare future Speech-to-Text integration

Technology:

- Python
- FastAPI

Planned endpoints:

```text
GET  /health
POST /media/upload
POST /media/transcribe
```

### Feedback Service

The Feedback Service creates an improved campaign version.

Responsibilities:

- Accept original campaign output
- Accept user feedback
- Generate improved campaign version
- Return version comparison data

Technology:

- Python
- FastAPI

Planned endpoints:

```text
GET  /health
POST /feedback/improve
```

---

## Demo Flow

The planned 3-minute demo flow:

1. Open KadriX.
2. Enter a product idea or upload demo-video context.
3. KadriX extracts the relevant product and campaign context.
4. Generate the first campaign draft.
5. Review the campaign preview in the dashboard.
6. Enter feedback.
7. Generate an improved second version.
8. Show the version comparison.
9. Briefly show how IBM Bob was used during development and where the exported Bob session reports are stored.

---

## Hackathon Deliverables

The final submission will include:

- Public demo video URL
- Written problem and solution statement
- Written IBM Bob usage statement
- Public repository URL
- Exported IBM Bob session reports in `/bob_sessions`

---

## Team

**Team name:** KadriX

This project is developed for the IBM Bob Dev Day Hackathon.

---

## Status

```text
MVP implementation complete. Preview video generation under validation.
```

**Note:** The creative-service exists and can generate preview videos, but MoviePy/ImageMagick rendering may require additional validation. A fix was attempted using DejaVu fonts, but rendering success should be verified before claiming full demo readiness.

**Recommended alternative if TextClip fails:** Generate slides with Pillow as PNG images and assemble with MoviePy ImageClip instead of using TextClip with ImageMagick.

---

## Future Improvements

Possible future improvements:

- IBM watsonx.ai integration for intelligent campaign generation
- IBM Speech-to-Text for automatic video transcription
- IBM Text-to-Speech for voiceover generation
- Campaign scoring and analytics
- Brand voice profiles
- PDF export
- Social media export formats
- Analytics-based campaign improvement
- Ad platform integrations
- User authentication and authorization

---

## License

This project is a hackathon proof of concept. License details may be added later.
