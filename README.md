# KadriX

KadriX is a Bob-built campaign workflow that turns rough product ideas, text briefs, and demo-video context into a launch-ready marketing direction.

The project is built for the **IBM Bob Dev Day Hackathon** under the challenge theme:

> Turn idea into impact faster

KadriX helps founders, solo builders, startups, and product teams move from "we have an idea or demo" to "we know how to talk about it" without needing a full creative agency workflow.

---

## What KadriX Does

KadriX provides a web-based campaign assistant with a WhatsApp-style user experience.

A user can submit:

- Product idea
- Short product description
- Campaign goal
- Target audience
- Desired tone of voice
- Optional demo-video context or transcript

KadriX then generates a campaign package containing:

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

Many small teams already have a product idea, prototype, app demo, or feature concept. The harder part starts when they need to turn that raw material into a clear campaign.

They still need to answer questions such as:

- What is the product really about?
- Who is the ideal audience?
- What is the strongest value proposition?
- Which campaign angle should be used?
- Which hooks and ad copies fit the product?
- How should the message change after feedback?

For small teams, this process is often slow, repetitive, and expensive.

---

## Solution

KadriX turns product input into structured campaign output through a simple feedback-driven workflow.

```text
Raw product idea or demo-video context
  -> product and audience understanding
  -> campaign generation
  -> campaign preview
  -> user feedback
  -> improved campaign version
```

The goal is to help builders move from idea to usable marketing output faster.

---

## MVP Scope

The hackathon MVP focuses on a stable and demonstrable proof of concept.

### Included

- Web-based WhatsApp-style chat interface
- Product brief input
- Optional demo-video upload flow
- Mock transcript or sample video context
- Campaign generation
- Campaign preview
- Feedback loop
- Improved campaign version
- Microservice-oriented backend structure
- IBM Bob session reports in `/bob_sessions`

### Not Included

- Real WhatsApp Business API integration
- Real ad publishing
- Full analytics dashboard
- Production-grade video editing
- User authentication
- Billing
- Kubernetes deployment

---

## IBM Bob Usage

IBM Bob is used as the core development partner for this project.

Bob helps with:

- Planning the MVP scope
- Designing the microservice-oriented architecture
- Creating backend services
- Building the frontend structure
- Implementing campaign generation logic
- Implementing the feedback loop
- Improving code quality
- Writing documentation
- Preparing the hackathon submission

IBM Bob is not required to be the runtime AI inside the final application. Instead, Bob is used as the main development partner to turn the idea into a working proof of concept faster.

Relevant exported IBM Bob task session reports and consumption summary screenshots will be stored in:

```text
bob_sessions/
```

---

## Optional IBM watsonx Usage

KadriX can optionally use IBM watsonx.ai as the runtime AI layer for campaign generation and campaign improvement.

Possible watsonx.ai use cases:

- Generate campaign strategy
- Generate hooks and ad copy
- Generate short video scripts
- Improve campaign output based on feedback
- Rewrite content for different tones

The MVP can also run with mock or template-based generation if watsonx.ai integration is not completed in time.

---

## Optional Video Understanding

KadriX supports the idea that users can provide demo-video context, such as a short app walkthrough or product screen recording.

For the MVP, video understanding can be simulated through a sample transcript or extracted product notes.

A future enhancement could use IBM Speech-to-Text to transcribe uploaded videos automatically.

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

The frontend provides the user-facing experience.

Responsibilities:

- WhatsApp-style chat interface
- Product brief form
- Demo-video upload UI
- Campaign preview
- Feedback input
- Version comparison

Technology:

- Vue 3
- Vite
- Tailwind CSS

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
Initial implementation phase.
```

---

## Future Improvements

Possible future improvements:

- Real WhatsApp Business API integration
- Real IBM Speech-to-Text transcription
- watsonx.ai runtime generation
- Campaign scoring
- Brand voice profiles
- PDF export
- Social media export formats
- Analytics-based campaign improvement
- Ad platform integrations

---

## License

This project is a hackathon proof of concept. License details may be added later.
