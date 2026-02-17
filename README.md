# Watchout - AI Travel Planner

An AI-powered travel itinerary planner for India, built with FastAPI, LangGraph, Gemini, Next.js, and MongoDB Atlas.

## 🌟 Features

- **Conversational Planning**: Chat with AI to plan your perfect trip
- **Multi-Agent System**: Specialized agents for itineraries, routes, stays, food, and weather
- **Real-Time Streaming**: SSE-powered chat with live updates
- **Smart Recommendations**: Personalized suggestions based on preferences
- **India-Focused**: Optimized for Indian destinations, transport, and cuisine
- **Robust Security**: Protected API endpoints and strict environment checks
- **Resilient UI**: Comprehensive error handling and user feedback systems

## 🛡️ Security Features
- **Token Management**: Auto-refresh authentication tokens
- **Environment Protection**: Dev bypass disabled in production
- **API Security**: Request timeouts and retry logic

## 🔔 User Experience
- **Toaster Notifications**: Integrated `sonner` for non-intrusive alerts
- **Error Boundaries**: Graceful fallback UI for runtime errors
- **Placeholder Pages**: Complete navigation structure

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance Python API framework
- **LangGraph** - Agent orchestration
- **Gemini 2.0 Flash** - LLM for intelligent responses
- **MongoDB Atlas** - Database with Vector Search
- **Firebase Auth** - Secure authentication

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Premium animations
- **Zustand** - State management

### Integrations
- Google Places API - Location data
- Mapbox - Routes and directions
- WeatherAPI - Weather forecasts
- Tavily - AI-powered search

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB Atlas account
- Firebase project
- API keys for integrations

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file and add your keys
cp .env.example .env

# Run the server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file and add your keys
cp .env.example .env.local

# Run the development server
npm run dev
```

## 📁 Project Structure

```
watchout/
├── backend/
│   ├── app/
│   │   ├── agents/       # AI agents (clarification, itinerary, etc.)
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Config, auth, security
│   │   ├── db/           # MongoDB, vector store
│   │   ├── models/       # Pydantic models
│   │   ├── tools/        # MCP tools (Places, Mapbox, etc.)
│   │   └── main.py       # Application entry point
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js pages
│   │   ├── components/   # React components
│   │   └── lib/          # Utilities, API client, stores
│   └── package.json
│
└── README.md
```

## 🔧 Environment Variables

### Backend (.env)
```
MONGODB_URI=mongodb+srv://...
GEMINI_API_KEY=...
FIREBASE_PROJECT_ID=...
GOOGLE_PLACES_API_KEY=...
MAPBOX_ACCESS_TOKEN=...
```

### Frontend (.env.local)
```
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## 📝 License

MIT License
