# Watchout - AI Travel Planner for India 🇮🇳

Watchout is a premium, AI-powered travel itinerary planner specifically designed for Indian travelers of all types—from luxury explorers to budget backpackers. Built with FastAPI, LangGraph, Groq, Next.js, and MongoDB Atlas.

## 🌟 Key Features

- **Conversational Planning**: A human-centric chat experience that simplifies the complexity of planning a trip.
- **Multi-Agent Orchestration**: A specialized fleet of agents (Supervisor, Clarification, Itinerary, Route, etc.) working in tandem.
- **Phase 4 AI Ops**:
  - **Prompt A/B Testing**: Deterministic variant assignment based on trip ID hashing.
  - **Hallucination Detection**: Real-time reviewer agent flags inconsistent or non-factual outputs.
  - **Token Caps**: Per-user daily usage limits for cost control and fairness.
- **Resilient Streaming**: Low-latency SSE-powered chat with automatic reconnection and exponential backoff.
- **India-Focused Intelligence**: Native knowledge of Indian states, transport (Trains/Flights/Taxis), and localized travel vibes.

## 🛡️ Security & Robustness

- **XSS Prevention**: Strict DOMPurify sanitization in the frontend markdown renderer.
- **IDOR Protection**: Consistent ownership validation across all `/trips` and `/chat` endpoints.
- **LLM Failover**: Automatic fallback to alternative providers (OpenAI) if primary (Groq) is degraded.
- **Tracing & Monitoring**: Full-stack OpenTelemetry integration with end-to-end trace propagation.

## 🛠️ Technology Stack

### Backend (Python)
- **FastAPI**: Main API framework.
- **LangGraph & LangChain**: State-aware agent orchestration.
- **Groq AI**: Primary inference engine (Llama-3.3-70b-versatile).
- **MongoDB Atlas**: Geo-spatial and vector storage.
- **Redis (Optional)**: High-performance rate limiting.

### Frontend (TypeScript)
- **Next.js**: React framework with App Router.
- **Tailwind CSS**: Modern utility-first styling.
- **Zustand**: Lightweight global state management.
- **Framer Motion**: Premium micro-animations and transitions.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.12+
- Node.js 20+
- MongoDB Atlas (Cluster with Vector Search)
- Firebase Project (Admin SDK credentials)

### 2. Installation

#### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## 📁 Repository Structure

```
watchout/
├── backend/          # FastAPI server & AI Agent architecture
│   ├── app/
│   │   ├── agents/   # Multi-agent logic (Supervisor, Itinerary, etc.)
│   │   ├── api/      # REST API routes
│   │   ├── core/     # Auth, Config, Rate limiters
│   │   ├── db/       # MongoDB connections
│   │   └── tools/    # External integrations (Mapbox, Places)
├── frontend/         # Next.js Application
│   ├── src/
│   │   ├── app/      # Page routes & Layouts
│   │   ├── components/# React UI library
│   │   └── lib/      # API clients & Stores
├── infra/            # Deployment & Infrastructure configs
└── README.md
```

## 📝 License
Distributed under the MIT License. See `LICENSE` for more information.

