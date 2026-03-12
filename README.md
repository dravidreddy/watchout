# Watchout - AI Travel Planner for India 🇮🇳

Watchout is a premium, AI-powered travel itinerary planner specifically designed for Indian travelers of all types—from luxury explorers to budget backpackers. Built with FastAPI, LangGraph, Groq, Next.js, and MongoDB Atlas.

## 🌟 Key Features

- **Conversational Planning**: A human-centric chat experience that simplifies the complexity of planning a trip.
- **Multi-Agent Orchestration**: A specialized fleet of agents (Supervisor, Clarification, Itinerary, Route, Food, Stay, Transport, Weather, Review) working in tandem.
- **Animated Route Map**: Live, interactive Mapbox GL map that appears alongside the chat showing the planned route with animated polyline, numbered city markers, and day-wise filtering.
- **Itinerary Preview**: Detailed day-by-day plan with activities, timing, costs, and notes, displayed as a slide-out panel.
- **Destination Suggestions**: AI-generated destination recommendation cards based on user preferences.
- **Phase 4 AI Ops**:
  - **Prompt A/B Testing**: Deterministic variant assignment based on trip ID hashing.
  - **Hallucination Detection**: Real-time reviewer agent flags inconsistent or non-factual outputs.
  - **Token Caps**: Per-user daily usage limits for cost control and fairness.
- **Resilient Streaming**: Low-latency SSE-powered chat with automatic reconnection and exponential backoff.
- **India-Focused Intelligence**: Native knowledge of Indian states, transport (Trains/Flights/Taxis), and localized travel vibes.

## 🗺️ Animated Route Map

The chat interface features a real-time animated map on the right panel:
- **Auto-triggered**: Appears when route data is streamed from the AI pipeline.
- **Route Visualization**: Purple polyline with glow effect connecting all destinations.
- **Day-Based Filtering**: Select specific days to view route segments and activity markers.
- **Numbered Markers**: Color-coded by day with popup details (stop name, city, day number).
- **Travel Animation**: Pulsing marker that animates along the route.
- **Responsive Layout**: 50/50 split on desktop, full-screen overlay on mobile with a Floating Action Button.

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
- **Mapbox API**: Route calculation and geocoding.
- **Google Places API**: Nearby attractions and restaurant recommendations.

### Frontend (TypeScript)
- **Next.js 14**: React framework with App Router.
- **Mapbox GL JS**: Interactive animated maps with WebGL rendering.
- **Zustand**: Lightweight global state management.
- **Framer Motion**: Premium micro-animations and transitions.
- **Firebase Auth**: User authentication and session management.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.12+
- Node.js 20+
- MongoDB Atlas (Cluster with Vector Search)
- Firebase Project (Admin SDK credentials)
- Mapbox account (Access token)

### 2. Installation

#### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
cp .env.example .env           # Configure API keys
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local     # Configure Firebase + Mapbox keys
npm run dev
```

### 3. Environment Variables

#### Backend (`.env`)
| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq inference API key |
| `MONGO_URI` | MongoDB Atlas connection string |
| `MAPBOX_ACCESS_TOKEN` | Mapbox API token for routing |
| `GOOGLE_PLACES_API_KEY` | Google Places API key |
| `FIREBASE_PROJECT_ID` | Firebase project for auth |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | Payment gateway credentials |

#### Frontend (`.env.local`)
| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL |
| `NEXT_PUBLIC_FIREBASE_*` | Firebase client SDK config |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | Mapbox public token for map rendering |
| `NEXT_PUBLIC_RAZORPAY_KEY_ID` | Razorpay frontend key |

## 📁 Repository Structure

```
watchout/
├── backend/                    # FastAPI server & AI Agent pipeline
│   ├── app/
│   │   ├── agents/             # Multi-agent logic (Supervisor, Itinerary, Route, etc.)
│   │   ├── api/                # REST & SSE API routes
│   │   ├── core/               # Auth, Config, Rate limiting, Token caps
│   │   ├── db/                 # MongoDB connection & collections
│   │   ├── models/             # Pydantic models (Trip, User, Itinerary)
│   │   ├── prompts/            # LLM prompt templates
│   │   └── tools/              # Mapbox, Google Places, Weather integrations
├── frontend/                   # Next.js Application
│   ├── src/
│   │   ├── app/                # Page routes & Layouts
│   │   ├── components/         # React component library
│   │   │   ├── chat/           # ChatInterface, RouteMap, ItineraryPreview
│   │   │   └── home/           # Landing page components
│   │   └── lib/                # API clients, Zustand store, utilities
├── infra/                      # Deployment & Docker configs
└── README.md
```

## 📝 License
Distributed under the MIT License. See `LICENSE` for more information.
