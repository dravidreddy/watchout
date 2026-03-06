# Watchout - AI Travel Planner for India
### Comprehensive Presentation Content Outline (25 Slides)
*Note for Presenter: Ensure the included `images/*` folder assets are placed appropriately on these slides.*

---

## Slide 1: Title Slide
**Title:** Watchout - AI Travel Planner for India
**Subtitle:** A Decentralized Multi-Agent System via Model Context Protocol
**Presenters:** Sanam Dravid Sharath Reddy, Vinodh Kumar V, Vaidish T
**Guide:** Dr. Babu Kumar S
**Institution:** CHRIST (Deemed to be University)
**Date:** March 2026

---

## Slide 2: Vision, Mission & Core Values
**Header:** Institutional Framework
**Bullet Points:**
- **Institutional Vision:** "Excellence and Service"
- **Mission:** Fostering holistic development for effective societal contributions.
- **Department Vision:** To excel in Human-Centred AI and Data-Driven Innovation.
- **Core Values:** Faith in God, Moral Uprightness, Social Responsibility, Pursuit of Excellence.

---

## Slide 3: Background - The Travel Planning Problem
**Header:** The Fragmented Travel Planning Landscape
**Visual Element suggestion:** Collage or icons showing scattered booking sites (Flights, Hotels, Transport, Trip Advisor).
**Text:**
- **Digital Overload:** Modern planning requires navigating a highly disjointed ecosystem.
- **Manual Labor:** Users search, compare, and consolidate details manually for individual travel logic nodes.
- **The Indian Context Challenge:** The market features varied transit modes, unpredictable latencies, and demands holistic experiential travel mapping not suitable for monolithic western engines.

---

## Slide 4: Motivation
**Header:** Why Build Watchout?
**Bullet Points:**
- **Eliminating User Frustration:** Replaces error-prone manual navigation with native constraint tracking.
- **Scaling True Personalization:** Moves beyond static listicles towards dynamic budgets and visual aesthetics.
- **Addressing AI Limitations:** Standard Large Language Models (LLMs) hallucinate factual realities. Watchout uses the Model Context Protocol (MCP) to verify boundaries.

---

## Slide 5: The Primary Architecture Problem
**Header:** LLMs vs. The $N \times M$ Integration Problem
**Visual Element suggestion:** *Figure 3.1: User Query Processing vs. Monolithic LLMs*
**Text:**
- **Context Saturation:** Feeding 50 flights and 50 hotels into an LLM window destroys conversational reasoning.
- **Geographic Hallucinations:** When unbounded, LLMs predict text, not reality (e.g., suggesting a 30-min Uber where a mountain pass blocks the road).
- **The $N \times M$ Problem:** Mapping $N$ user dialogues to $M$ external APIs requires unmaintainable hard-coded prompt templates.

---

## Slide 6: Watchout - High Level Overview
**Header:** A "Smart Travel Agent"
**Visual Element suggestion:** *Figure 1.1: Watchout High-Level Conceptual Workflow*
**Text:**
- **Decentralized Multi-Agent Ensemble:** Replaces single monolithic prompting.
- **Model Context Protocol (MCP):** Secures data exchange amongst Agents and External APIs.
- **Persistent Vector Memory:** ChromaDB automatically retains implicit references.

---

## Slide 7: Literature Review & Identified Gaps
**Header:** Evolution of Recommender Systems
**Table Element:** (Simplified from Table 2.1)

| Methodology | Application Example | Identified Primary Limitation |
| :--- | :--- | :--- |
| **Collaborative Filtering** | TripRec (2019) | Fails to scale with real-time location alterations and temporal constraints. |
| **Monolithic LLMs** | Standard ChatGPT | Highly prone to factual and physical hallucinations. |
| **Proposed:** Multi-Agent + MCP | **Watchout Platform** | **Overcomes Both:** Replaces rigid optimization with flexible conversation grounded purely in verified real-world limits. |

---

## Slide 8: Advancing over Monolithic LLMs
**Header:** The Importance of Explicit Parameters
**Visual Element suggestion:** A diagram comparing a "Guessing AI" vs. Watchout's "Fetching AI".
**Text:**
- **The Central Innovation:** Treating external REST APIs as standardized "Servers" and the sub-agents as structured "Clients."
- **Mitigating Malformed Prompts:** Halts exploratory AI from passing invalid syntax (wrong dates or city codes) before it reaches actual payment APIs.
- **Zero Hallucination Guarantee:** Final schedule text is assembled solely from pre-approved JSON endpoints.

---

## Slide 9: Hardware & Software Requirements
**Header:** System Specifications
**Table Element:** (Derived from Tables 4.1 & 4.2)

| Component Level | Technology Stack Executed |
| :--- | :--- |
| **Backend Core** | Python 3.10+, FastAPI, Uvicorn (ASGI Framework) |
| **Frontend UI** | Next.js 14, React.js (TypeScript), Context State Variables |
| **AI Orchestration**| LangChain / LangGraph Engine |
| **LLM Deployment** | Ollama via local Llama-3.1-8B (RTX 3060+ Acceleration) |
| **Persistent Data** | MongoDB (Document schema), ChromaDB (Vector semantics) |

---

## Slide 10: Watchout System Architecture
**Header:** Watchout N-Tier System Design
**Visual Element suggestion:** *Figure 4.1: Watchout N-Tier System Architecture*
**Text:**
- **Presentation Tier:** Next.js Server-Sent Events (SSE) streaming state.
- **Logic Tier:** FastAPI receiving concurrent payloads routing to the LangGraph executor.
- **Execution Tier:** MongoDB sessions, ChromaDB memories, and live MCP Server APIs.

---

## Slide 11: Agent Architectures & Roles
**Header:** Specialized Sub-Routine Responsibilities
**Table Element:** (Derived from Table 4.3)

| Agent Node | Primary Functionality | API Endpoint Triggered via MCP |
| :--- | :--- | :--- |
| **Orchestrator Agent** | Parses initial vague constraints; routes execution graphs. | *None directly* |
| **Flights Agent** | Filters global datasets by exact routing & price vectors. | `skyscanner.get_flights` |
| **Hotels Agent** | Retrieves localized geo-lodgings matching star ratings. | `amadeus.find_hotels` |
| **Itinerary Agent** | Formulates transit matrix mappings based on hotel origins. | Google Places Matrix |

---

## Slide 12: Data Flow inside the Graph
**Header:** LangGraph State Transitions
**Visual Element suggestion:** *Figure 4.2: Decentralized Multi-Agent Architecture using LangGraph*
**Text:**
- **Replacing 'If-Else' Mess:** Utilizes an acyclic directed graph mathematically verifying transition capabilities.
- **TypedDict State Array:** Values are explicitly enforced. (e.g., `flight_objects: Optional[List[dict]]`).
- **Synchronized Routing:** The final Itinerary generation halts iteratively until **both** Flight and Hotel API loops confirm completion.

---

## Slide 13: Data Flow Diagrams
**Header:** DFD Level 0 & 1
**Visual Element suggestion:** *Figure 4.4: Data Flow Diagram (DFD) - Level 0* **AND** *Figure 4.5: Data Flow Diagram (DFD) - Level 1* (Side-By-Side)
**Text:**
- **Context (Level 0):** Unstructured user constraints evaluated into perfectly formatted itineraries.
- **Sub-Processes (Level 1):** Vector Grounding -> Parallel LangGraph Querying -> External API Reconciliation.

---

## Slide 14: Action Sequences
**Header:** Execution Flow & Asynchronous Endpoints
**Visual Element suggestion:** *Figure 4.7: Sequence Diagram: User Query to Full Itinerary*
**Text:**
- Post request to `/api/chat` -> State Graph initialized.
- Secure tool payloads crafted targeting Amadeus and Skyscanner wrappers.
- Returning JSON objects appended to the internal state variable sequentially.

---

## Slide 15: Overcoming Model Amnesia 
**Header:** The ChromaDB Memory Pipeline
**Visual Element suggestion:** *Figure 5.1: E-R Diagram for MongoDB and Vector Database Memory Schema*
**Text:**
- **Vector Embeddings (all-MiniLM-L6-v2):** Raw Strings stored dynamically as coordinate distances.
- **Passive Context Appendage:** Sourcing nearest historic intent vectors (e.g., user usually prefers Window seats) from that user's specific collection profile.
- Re-injects variables system-side seamlessly without alerting the GUI front-end.

---

## Slide 16: Code Implementation Preview
**Header:** Graph Initialization 
**Visual Element suggestion:** *Figure 6.1: LangGraph Edge/Node Transition State Machine Code View*
**Code Snippet Highlights:**
```python
workflow = StateGraph(TripPlanState)
workflow.add_node("flights_agent", flights_agent_node)
workflow.add_node("hotels_agent", hotels_agent_node)
# Complex Routing enforced natively
workflow.add_edge(["flights_agent", "hotels_agent"], "itinerary_generator")
```

---

## Slide 17: User Interface & Server-Sent Events
**Header:** Streaming Generations via Next.js
**Visual Element suggestion:** *Figure 7.2: User Interface - Chat Stream with SSE Responses* 
*(Alternatively, insert a brief recorded video clip demonstrating the real-time UI stream generating text and cards concurrently).*
**Text:**
- **Mitigating Load Pings:** Solves the immense UX delay of waiting for 5 APIs to run linearly.
- Fast-streams chunks backwards akin to standard ChatGPT interaction dynamics utilizing native Python `EventSourceResponse`.

---

## Slide 18: System Testing - Unit Validations
**Header:** Verifying Granular Component Safety
**Table Element:** (Highlighting critical test metrics)

| Test Module Target | Failure Scenario Assessed | Result Validation Output |
| :--- | :--- | :--- |
| **API Backend** | SQL Injection payload interception. | Caught universally by FastAPI Pydantic parsing. |
| **State Nodes** | Null Destination routing. | Agent paused safely; actively requested Origin from user. |
| **External Integrations**| Amadeus API returns 500 Network Code | MCP Wrapper triggers immediate failover fallback state seamlessly. |

---

## Slide 19: System Testing - Complex Constraint Validation
**Header:** Ensuring End-to-End Success & "Red Teaming"
**Text:**
- **Strict Boundary Execution Test:** "Plan an active trip to Manali for 3 days under ₹15,000 totality including flights."
  - Output respected rigid boundary metrics strictly scraping exactly ₹12,000 flight arrays prior to compilation.
- **The Red Team Test (Hallucination Probe):** "Generate a flight schedule directly connecting Jaipur's internal network to an active underwater base."
  - Output halted inherently; Agent gracefully confirmed geographic impossibility rather than inventing a path.

---

## Slide 20: Result Analytics (1)
**Header:** Quantitative System Analysis
**Visual Element suggestion:** *Figure 8.1: Performance Chart: Task Success Rate vs. Complexity*
**Table Element:** (Derived from Table 8.1)

| Evaluation Metric | Measured Output Result |
| :--- | :--- |
| **Task Success Rating** | **94.2%** (Errors strictly network timeout related, not logic) |
| **System Latency Baseline** | **P50 Generation Round-trip latency (12.5s)** |
| **Hallucination Occurrence**| **0.0% Geographic Invention Factor** |

---

## Slide 21: Result Analytics (2)
**Header:** Addressing Baseline API Latency
**Visual Element suggestion:** *Figure 8.2: Performance Chart: Latency vs. Node Execution Time*
**Text:**
- Integrating local inference (Ollama) against external parallel data sources inevitably scales timing metrics.
- The tradeoff—trading sheer generation speed for absolute logistical perfection—is validated via SSE frontend streaming buffering visually.

---

## Slide 22: Discussion: The MCP Triumph
**Header:** Validating the Protocol Architecture
**Text:**
- Operating without the Model Context Protocol definitively reproduced rampant hallucinated destinations across non-verified geographic zones (e.g., claiming Ooty possessed a massive international flight hub).
- Locking the conversational agent behind strict verification boundaries successfully isolates NLP variables from standard Database parameters.

---

## Slide 23: Application Demo 
**Header:** Watchout in Action
**Visual Element suggestion:** *Placeholder for Live Platform Demonstration Video or High-Resolution UI Montage displaying End-to-End Flow: Login -> Query -> Agent Stream -> Iteration -> Complete Output.*

---

## Slide 24: Conclusion
**Header:** Elevating Modern Travel Architecture
**Bullet Points:**
- **Bridged the Core Divide:** The Watchout platform replaces strict rigid HTML travel websites with an incredibly flexible natural LLM model possessing none of the standard hallucination pitfalls.
- Validates a deploy-ready pipeline designed exclusively to support multi-user operations securely.

---

## Slide 25: Future Enhancements & Trajectory
**Header:** Beyond the Current Implementation
**Bullet Points:**
- **UPI Integrations:** Connecting localization loops dynamically executing final transactions inside the agent session array.
- **Deep Transit Routing:** Engaging ONDC or Local State Bus API feeds linking hyper-rural connections previously inaccessible.
- **Immersive Offloading:** Exporting graph mapping parameters directly matching user-generated constraints into active real-world Augmented Reality phone overlays.
- **Passive Automation:** Expanding Instagram OAuth frameworks to scrape public photo stylistic tags for completely zero-click profile generations.
