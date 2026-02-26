# Watchout Indian AI Travel Planner

## PROJECT REPORT

**In partial fulfillment of the requirements for the award of the Degree of Bachelor of Technology / Science**

### Submitted By:
1. **Sanam Dravid Sharath Reddy** - 2262142  
2. **Vinodh Kumar** - 2262172  
3. **Vaidish T** - 2262180

### Under the guidance of:  
**Dr. Babu Kumar S**

---

<div style="page-break-after: always;"></div>

## DECLARATION  
We, Sanam Dravid Sharath Reddy (2262142), Vinodh Kumar (2262172), and Vaidish T (2262180), declare that the project report entitled “Watchout – AI Travel Planner for India” submitted to University/College, constitutes an original work done by us under the supervision of Dr. Babu Kumar S, and this project work hasn’t been submitted to any other body for the award of any other degree or diploma.  
**Place:**  
**Date:**

<div style="page-break-after: always;"></div>

## CERTIFICATE  
This is to certify that this project report entitled “Watchout - AI Travel Planner for India” is a bonafide record of the project work carried out by Sanam Dravid Sharath Reddy (2262142), Vinodh Kumar (2262172) and Vaidish T (2262180) under my supervision and guidance.  
___________________________                     ___________________________  
**Signature of the Guide**                          **Signature of HOD**  
Dr. Babu Kumar S

<div style="page-break-after: always;"></div>

## ACKNOWLEDGEMENT  
Our adviser, Dr. Babu Kumar S (our guide), we thank for his support, guidance, constructive criticism, and advice. And last but not least, we also thank the Department and Institution for providing infrastructure and resources that supported our work to be completed successfully. Lastly, we are very grateful to thank our parents and friends.  

<div style="page-break-after: always;"></div>

## ABSTRACT  
Given how quickly the travel industry is reviving and access to digital travel tools has become widespread, trip planning now seems harder (if that ever was the case) given the sheer volume of information on offer. The need for different cultures and geographies such as India makes it difficult to regularly book and plan travel using the same tools. **Watchout:** An advanced AI travel itinerary planner for Indian travelers. With multi-agent orchestration built into LangGraph, Fast API, Groq AI (Llama 3), and Next.js, Watchout offers a highly conversational, human-centric chat. This platform works with advanced AI agents; the specialized agents of the organization (Supervisor, Clarification, Itinerary, Route, Food, etc.) to automatically create, revise, and run personalized itineraries to match users’ goals — budget, travel style, regional preferences, etc. Notable features also include Phase 4 AI Ops with Prompt A/B testing, real-time hallucination detection, live token management, robust SSE streaming, Multimodal AI screenshot analysis for itinerary generation, and a Payment Gateway for monetized tiers/bookings. For the backend, we implement MongoDB Atlas for geo-spatial and vector stores, so it can rapidly recall local Indian transport, places, and travel vibes. The system architecture, design methodology, implementation phases, comprehensive testing strategies, and methodologies of the system are described in depth in this report with the intention of enabling the system to deliver an exceptionally scalable, secure, and scalable web application.  

<div style="page-break-after: always;"></div>

## TABLE OF CONTENTS  
1. Introduction  
2. Literature Review  
3. System Analysis  
4. System Design  
5. Implementation  
6. Testing  
7. Results & Discussions  
8. Conclusion & Future Scope  
9. References  

<div style="page-break-after: always;"></div>

---

## CHAPTER 1: INTRODUCTION  
It’s a huge travel industry; from booking flights to reserving hotels or booking trains to planning daily itineraries, people need to keep track of everything. There is no obvious yet simple fully automated and AI-driven solution that is able to capture the rich intricacies of Indian travel — such as train availability predictability, how familiar the food culture or restaurants are, budgets can be utilized flexibly by combining different plans or real-time route constraints. The platform “Watchout” aims to fill this niche by providing an intelligent conversational system that plays the important role of an expert in local travel.  

### 1.2 Problem Statement  
Despite the existence of travel portals (MakeMyTrip, Yatra, Agoda), for most users, it is still a painstaking effort to find and cross-check information to create a coherent itinerary. This process requires extensive effort and is prone to human error. Current chatbot deployments in travel still rely heavily on decision trees instead of conversational AIs. Another significant area is an integrated platform that interprets vague user intentions (e.g., “I want to have a budget holiday in South India for a 3-day beach trip”) into structured plans that can be executed into concise plans within reasonable time constraints.  

### 1.3 Objectives  
- Developing a multi-agent AI system to handle complicated travel queries.  
- Build a native knowledge base of Indian geography, transport networks (IRCTC, Flights, Inter-city cabs), and local user experiences.  
- Build a responsive and modern UI with Next.js, Framer Motion, and Tailwind CSS. – Enterprise-level security, hallucination detection, and prompt A/B testing (Phase 4 AI Ops). – To enable Multimodal AI Vision capabilities for "Screenshot-to-Itinerary" location extraction. – Payment Gateway integration to process secure payments. This will provide a user authentication mechanism, a conversational chat interface, and a database for agentic backend orchestration. In addition, data persistence in MongoDB allows processing user-uploaded screenshots for travel extraction. This is also responsible for payment processing and error handling. Upcoming versions (out of scope): Deep Direct Bookings, AR Navigation, live weather tracking. ---  
<div style="page-break-after: always;"></div>  
## Chapter 2: LITERATURE REVIEW  
The OTAs, by and large, are aggregators. They depend on users to enter precise dates and places and filter through hundreds of choices. TripAdvisor, and the like, are all reviews, not automated planning tools, without automated planning abilities. Recently, ChatGPT is widely used as a means for generating itineraries that do not support live validation, merging of user profiles, and user preference memory across multiple sessions.  

GPT-4, Llama-3, and other classical LLMs have transformed NLP. But general LLMs have also “hallucinated” inaccessible hotels or physical impediments to connected trains (like proposing a 1-hour train trip between 500 km-away cities). This would need another system for LLM generation, limiting LLM generation from present data that could be used with logical semantics. For one, single-prompt LLMs would be of poor performance as the context window begins to fill. Multi-Agent frameworks, such as LangGraph, offer concern separation. One agent is named Supervisor and can delegate functions to smaller sub-agents (Routing Agent, Food Agent, Itinerary Agent etc.). One agent has the responsibility to distribute work so that responsibilities can be transferred to sub-agents and increase accuracy and factual correctness massively.  
### 2.4 Gap Analysis  
The most evident gap in the current ecosystem is the absence of context-aware hyper-localized AI planners for India, which similarly have safety guardrails (hallucination detection) and cost controls (token caps). Watchout fills this gap between regionally-based logic and LangGraph state machinery.  
### 3.1 Requirement Gathering  
First, I want to talk about user fatigue in traveling and the fatigue experienced. The questionnaire was formulated to answer such questions as:  
I: How do you feel about planning the next adventure? Any AI tools have limitations described as too simple to lead you through the process.  
### 3.2 Functional Requirements  
1. **User Authentication:** Secure login/registration with Firebase Auth.  
2. **Conversational Interface:** AI chat in real time using Server-Sent Events (SSE).  
3. **Trip Generation:** AI has to be able to make personalized daily itineraries.  
4. **Agent Orchestration:** They also need routing queries to agent entities.  
5. **Memory Management:** System to hold historical chat context from session.  
6. **Screenshot Analysis:** Users can upload screenshots of travel content (e.g., reels, posts) for the AI to extract destinations, descriptions, and hashtags using Vision models, followed by user confirmation.  
7. **Payment Gateway:** Must be ready to accept payment for premium functionality or even for booking directly with the client.
#### 3.3 Non- Functional Requirements.  
**Performance:**  
- The SSE stream must start outputting the responses in 1-2 seconds.  
(2) **Scalability** The backend will need to be able to access many multiple connections to websocket/SSE in parallel asynchronously (driven by FastAPI).  
3. **Security:** The efficient XSS detection has been well built with DOMPurify and IDOR protection on API endpoints.  
**Reliability:** Failover from primary (Groq) to secondary (if degraded).  
**Cost Control:** With token limiting per user LLM to very little extent its use can be constrained.  
### 3.4 Hardware and Software Specifications  
- **Client Side (Minimally):** The client’s current web browser (Chrome, Firefox, Safari), 4GB RAM.  
- **Server Side (Deployment):** Linux Server, 2+ CPU Cores, 4GB RAM minimum for FastAPI/Uvicorn.  
- **Frontend Tech Stack:** Next.js (App Router), TypeScript, Tailwind CSS, Zustand, Framer Motion.  
- **Backend Tech Stack:** Python 3.12+, FastAPI, LangGraph, LangChain, Groq AI (Llama-3).  
- **Database:** MongoDB Atlas (Vector Search support)  
---  
<div style="page-break-after: always;"></div>

## CHAPTER 4: SYSTEM DESIGN  
### 4.1 Architecture Overview  
Watchout follows a decoupled microservices-like design, but is managed as a monolithic FastAPI backend and Next.js (frontend) with REST APIs and SSE streams.  
- **Frontend Tier:** The UI/UX, local state management (Zustand), and streaming render of markdown in realtime.  
- **Backend Tier:** FastAPI sends incoming requests to LangGraph executor.  
- **AI Tier:** A state machine named LangGraph orchestrates the query across various LLM agents.  
- **Data Tier:** User profiles, trip metadata, chat history, vector embeddings stored in MongoDB Atlas.  
**Input:** User submits a prompt.  
**Supervisor Agent:** Considers the prompt and decides about Clarification, Itinerary creation, Route planning, or generic chat.  
**Sub-Agents:**  
   - *Itinerary Agent:* Provides day-to-day plans.  
   - *Route Agent:* Calculates distances and means of transportation.  
   - *Food Agent:* Recommends the right foods for a particular area.  
**Reviewer Agent (Hallucination Detection),** correlates outputs with factual validity. If that fails, it moves to the agent responsible for regeneration.  
**Output:** The returned response then which once is verified is streamed back to the frontend.  
### 4.3 Database Schema (MongoDB Collections)  
1. **Users:** _id, email, firebase_uid, created_at, token_usage, subscription_tier  
2. **Trips:** trip_id, user_id, destination, start_date, end_date, status, screenshot_metadata.  
3. **Messages:** message_id, trip_id, role (user/assistant), content, timestamp.  
4. **Transactions:** txn_id, user_id, amount, status, gateway_response, timestamp.  
### 4.4 Data Flow Diagram (DFD)  
**Level 0 (Context Level):**  
User → [Watchout Web App] ↔ Backend API → MongoDB Document DB  
LLM Provider (Groq) <-> Backend API  
Payment Gateway (Razorpay/Stripe) <-> Backend API  
Vision AI Provider (Multimodal LLM) <-> Backend API  
### 4.5 UI/UX Design  
The UI/UX is quite modern, minimalist, high end design.  
- It was made using the standard API and UI/UX based on our design model for all internal content. Framer Motion emphasizes typography, lots of white space, and micro-interactions. This design reduces cognitive overhead since the chat interface sits in centre with sidebars for the Trip History & Profile Setup.  
---  
<div style="page-break-after: always;"></div>  
## CHAPTER 5: IMPLEMENTATION

### 5.1 Frontend Implementation  
Frontend was developed with Next.js 14+ (App Router).  
- For the lightweight state management instead of redux boilerplate, we leverage **Zustand**.  
- **Tailwind CSS** is used to create the design, which makes it quick to iterate UI parts without utilizing inline CSS.  
- **Streaming Chat UI:** The use of standard Web APIs (fetch with ReadableStream), parsed the chunks, and updated the React state for typing effect.  
- **Markdown Rendering:** React Markdown wrapped in DOMPurify, where no scripts have gotten injected into LLM output by malicious code.  
### 5.2 Backend Implementation  
- **FastAPI Setup:** Fastest ever async endpoints;  
Uvicorn is the ASGI server.  
- **LangGraph Integration:** A state type TypedDict, and edges/nodes. The cyclic graph permits the Reviewer agent to reject outputs and return to the generation agents until a finite recursion limit is achieved, preventing infinite looping.  
- **AI Ops (Phase 4):**  
- *A/B testing:* Added a hashing function on the trip_id. If hash(trip_id) % 2 == 0, System Prompt A is applied; otherwise System Prompt B is assigned. This facilitates data-driven optimization of AI directions.  
- *Token Limits:* The Middleware intercepts user requests, logs that a user does the requests, checks user’s token count to MongoDB, then increases the token count based on response metadata of the LLM. If daily max is reached, a 429 Too Many Requests response is served.  
- **SSE Streaming:** EventSourceResponse in FastAPI creates chunks generated by LLM for live UIs. 

### 5.3 Screenshot-to-Itinerary Integration  
To bypass strict anti-scraping mechanisms and improve reliability, a "Screenshot-to-Itinerary" module powered by Multimodal AI has been established. - Users can upload a screenshot of any travel-related content (such as an Instagram reel, YouTube short, or blog post). - The backend securely passes this image to a Multimodal Vision LLM to perform OCR and visual analysis.  
- The AI extracts visible constraints, locations, hashtags, and descriptions. - **Verification Step:** The system prompts the user to explicitly verify if the detected place is correct before proceeding with itinerary generation.  

### 5.4 Payment Gateway Integration  
Monetisation (e.g., purchase of token packs, premium trip generation or booking commissions) leverages a strong payment gateway (e.g., Razorpay/Stripe module) to process user intent into transactions. 1. User chooses a special action for premium. 2. Frontend requests Order ID from the FastAPI backend. 3. Backend creates an order with the Payment Provider API and returns Order ID. 4. Payment modal of the payment is initialized by Frontend. A webhook or frontend callback informs the backend upon success/failure. 5. The backend checks the signature/token and also changes users account status (e.g., access premium tokens) with MongoDB.  
<div style="page-break-after: always;"></div>

## CHAPTER 6: TESTING

### 6.1 Unit Testing  
- **Backend:** You use pytest to test utility functions (token counters, prompt hash algorithms (A/B testing), string parsers etc.) using their own utility functions. - **Frontend:** Component testing with Jest & React Testing Library makes sure that components like Chat Input, Markdown Renderer, Payment Modals are properly rendered and do not crash.  

### 6.2 Integration Testing  
- API Endpoints are analyzed using FastAPI TestClient. - LangGraph flows are also generated using mock LLM responses in the test, so the state machine can route correctly (e.g., for food request to Food_Agent). Payment Gateway webhooks are emulated including POST requests to verify signature processing and database updates.  

### 6.3 System & End-to-End Testing  
- Full user flow from Registration -> Login -> Trip Creation -> Chatting with AI -> Uploading a Screenshot and Verifying Location -> Payment was manually tested in multiple browsers (Chrome, Safari, Firefox) and simulated network conditions.  

### 6.4 AI Specific Testing  
- **Hallucination Testing:** Purposeful insertion of invalid prompts to check if the Reviewer Agent was flagging and correcting the output correctly. - **Load testing:** Used locust/k6 (refer to repo) to simulate multiple hundreds of concurrent SSE connections to verify Uvicorn behaves as intended.  
---  
<div style="page-break-after: always;"></div>  

## CHAPTER 7: RESULTS AND DISCUSSIONS  

### 7.1 Outcomes  
The result is multi-turn intricate conversations on travel with major Indian destinations that are successfully executed. It’s context-holding in the app so a user isn’t going to just try it again and again. The proposed method is considered high scalability as it provides fast SSE streaming and provides very low latency, and therefore performance. We can see the following benefits of implementing a Multi-Agent Orchestration Based Approach: SSE streaming implementation achieves an 85% improved perceived latency and no longer needs the same HTTP response as standard. - Multi-agent orchestration led to response accuracy on Indian transit networks significantly better than a standard zero-shot LLM methodology.  

### 7.2 UI Evaluation  
The Framer Motion animations provide vital visual feedback when AI generation states apply.  

### 7.3 Performance Metrics  
- **Average API Response Time (stream starts):** ~1.2s  
- **Database query average time:** ~45ms for fetching chat history  
- **Agent Orchestration Overhead:** ~400ms  

### 7.4 Discussion on AI Ops  
This was very handy – it helped me learn formatting on prompt A/B test. Because users preferred itineraries in bullets and clear markdown headers rather than using narrative paragraphs, their itinerary choices were factored into the main system prompts. Token caps also helped prevent abuse and kept infrastructure costs predictable. The integration of Multimodal Vision capabilities and the Payment Gateway takes the project from a tech demo to a practical deploy and monetization environment.  
---  
<div style="page-break-after: always;"></div>

## CHAPTER 8: CONCLUSION AND FUTURE SCOPE  

### 8.1 Conclusion  
The “Watchout - AI Travel Planner” is a very successful show that how sophisticated LLM orchestration (LangGraph) can be deployed to solve real, highly localized logistical challenges. The project can serve as an effective proof-of-concept, as AI powered platforms can effectively simulate a travel experience on real time with very tight scheduling constraints. Using a microservices mindset in a strong FastAPI and Next.js framework, the system works, is stable and user-centered. The addition of Phase 4 AI Ops makes the system reliable, factually correct, and economically viable and the AI Vision and Payment integrations create instant business value as well as bridges user identity.  

### 8.2 Future Scope  
Though the current release is quite powerful, it can be enhanced with the following additions to support the platform:  
1. Implementing **Direct Integrations & Bookings (API):** Integrating with existing systems like MakeMyTrip, Cleartrip, IRCTC to directly book an invite from your chat interface  
2. **Real-time Weather & Alerts:** Utilization of open weather APIs to adjust itinerary dynamically based on the weather (e.g., indoor inactivity if it rains).  
3. **Augmented Reality (AR) Navigation:** Mobile version with AR overlays to show consumers local market, or heritage monument, according to planned itinerary.  
4. **Collaborative Trip Planning:** Allows multiple users to log in to a 'Trip Room' and converse concurrently with the AI.  
5. **Advanced Multimodal Features:** Expanding the vision capabilities to process user-uploaded videos or continuously learn from user visual preferences.  
---  
<div style="page-break-after: always;"></div>

## REFERENCES  

1. FastAPI Documentation: https://fastapi.tiangolo.com/  
2. Next.js App Router Documentation: https://nextjs.org/docs  
3. LangChain and LangGraph Docs: https://python.langchain.com/  
4. MongoDB Atlas Vector Search: https://www.mongodb.com/products/platform/atlas-vector-search  
5. Groq AI Compute: https://groq.com/  
6. Tailwind CSS Framework: https://tailwindcss.com/  
7. Razorpay / Stripe API Documentation (Payment Integration Guidelines)  
8. Vision Models / Multimodal LLM Documentation  
9. "Attention Is All You Need" - Vaswani et al. (Foundation of modern LLMs)  
---  
*End of Report*