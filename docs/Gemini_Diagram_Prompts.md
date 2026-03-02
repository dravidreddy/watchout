# AI Prompts for Generating Report Figures in Eraser.io

Eraser.io has a built-in AI assistant. Instead of asking Gemini for code, you can literally copy the text inside the quote blocks below and paste it directly into the **"Generate Diagram from Prompt"** box inside Eraser.io to build these diagrams instantly.

---

## 1. Figure 1.1: Watchout High-Level Conceptual Workflow
**Eraser AI Prompt to Copy:**
> "Generate a top-to-bottom flowchart representing an AI Travel Planner called Watchout. Start with a 'User' node that points to a 'Next.js Frontend' block. Connect the frontend to a 'FastAPI Backend' block, labeled with 'SSE Streaming'. From the Backend, connect to a 'LangGraph Orchestrator' node. The Orchestrator should branch out to three separate sub-agent nodes: 'Flights', 'Hotels', and 'Itinerary'. Group those three sub-agents and connect them down to an 'External APIs' block (Skyscanner, Amadeus, Maps) through a boundary labeled 'Model Context Protocol (MCP)'. Make the final output point back up to the User as a 'Validated Itinerary'."

---

## 2. Figure 3.1: User Query Processing vs. Monolithic LLMs
**Eraser AI Prompt to Copy:**
> "Create a comparison flowchart with two separate, large groups side-by-side. Name the left group 'Traditional Monolithic LLM'. Inside it, put a single 'ChatGPT' node. Have 6 different nodes around it (API 1, API 2, etc.) all pointing arrows furiously into the single ChatGPT node. Make an arrow from ChatGPT point to an outcome node called 'Context Overflow & Hallucinations'. 
> Name the right group 'Watchout Multi-Agent Approach'. Inside it, put a 'Trip Orchestrator', pointing to two distinct agents ('Flight Agent', 'Hotel Agent'). Have each agent point to only ONE specific API node. Connect the end of this flow to a green node called '100% Deterministic Accuracy'."

---

## 3. Figure 4.1: Watchout N-Tier System Architecture
**Eraser AI Prompt to Copy:**
> "Generate an N-Tier System Architecture block diagram for an application. Create 4 main horizontal groups stacked on top of each other. 
> Top group: 'Presentation Tier' containing nodes for Next.js, React, and Zustand. 
> Second group: 'Logic/Application Tier' containing FastAPI and LangGraph. 
> Third group: 'Agent/Execution Tier' containing Ollama Llama 3, Flights Agent, Hotels Agent, and MCP Servers. 
> Bottom group: 'Data & Memory Tier' containing MongoDB, ChromaDB Vector Embeddings, and External APIs. 
> Draw top-down arrows connecting the tiers to show the flow of data."

---

## 4. Figure 4.2 & Figure 6.1: LangGraph Agent State Machine
**Eraser AI Prompt to Copy:**
> "Create a state diagram flowchart. Start with a 'Play' icon node called 'START'. Point it to an 'Orchestrator Node'. Make the Orchestrator split into two parallel paths: one going to 'Flights Agent' and the other to 'Hotels Agent'. Have both of those paths reconverge into a single node called 'Sync Wait State'. From the Wait State, draw an arrow to 'Itinerary Generator'. Finally, point that to a 'Check' icon node called 'END'. Add short descriptive labels on the arrows explaining the flow of JSON data."

---

## 5. Figure 4.3: Model Context Protocol (MCP) Integration
**Eraser AI Prompt to Copy:**
> "Generate a simple sequence or flowchart diagram showing how the Model Context Protocol (MCP) works. Create a node labeled 'Watchout Sub-Agent (Client)'. Connect it with a bi-directional arrow labeled 'JSON-RPC Tool Call' to a group called 'MCP Server Container'. Inside the container, put a node called 'Schema Mapper'. Have the MCP Server group point to a final node called 'Amadeus External API' labeled 'Authenticated HTTP REST Call'. Add a text note near the MCP server saying 'API Keys remain hidden here'."

---

## 6. Figure 4.4 & 4.5: Data Flow Diagrams
**Eraser AI Prompt to Copy:**
> "Create a Level 1 Data Flow Diagram (DFD) using flowchart syntax. Start with an external entity node called 'User'. The User sends 'Trip Constraints' into a process node '1.0 Parse Query'. Connect 1.0 to a database node named 'D2: ChromaDB Vector Store' to retrieve memory. Connect 1.0 to a process node '2.0 Delegate Agents'. Connect 2.0 to a process node '3.0 Execute Tool Constraints via MCP'. Have 3.0 pull from an external entity 'Live API Feeds'. Connect 3.0 to '4.0 Synthesize Narrative', which stores data in database 'D1: MongoDB'. Send the final itinerary from 4.0 back to the User."

---

## 7. Figure 4.6: UML Use Case Diagram
**Eraser AI Prompt to Copy:**
> "Generate a UML Use Case Diagram. On the left, put two Actor icons: 'Traveler' and 'System Admin'. On the right, draw a large system boundary box labeled 'Watchout Travel Planner'. Inside the box, drop these use cases as oval nodes: 'Authenticate Account', 'Input Trip Constraints', 'Link Instagram Profile', 'View Live SSE Stream', and 'Purchase Premium Tokens'. Draw simple connecting lines from the Traveler actor to all of these use cases. Connect the Admin actor only to an 'Observe Traffic' use case."

---

## 8. Figure 4.7 & Figure 7.3: Sequence Diagram
**Eraser AI Prompt to Copy:**
> "Create a highly detailed sequence diagram using Eraser sequence syntax. The participants across the top should be: User, NextJS, FastAPI, ChromaDB, LangGraph, MCP_Server, and External_APIs.
> Sequence steps: User submits prompt to NextJS. NextJS opens SSE connection to FastAPI. FastAPI queries ChromaDB for past preferences. ChromaDB returns vectors to FastAPI. FastAPI triggers LangGraph Orchestrator. LangGraph requests Flights from MCP_Server. MCP_Server translates and hits External_APIs. APIs return JSON to MCP_Server. MCP_Server returns data to LangGraph. LangGraph generates final output to FastAPI. FastAPI streams SSE chunks back to NextJS."

---

## 9. Figure 5.1: Database E-R Diagram
**Eraser AI Prompt to Copy:**
> "Generate a database Entity-Relationship (ER) Diagram block structure. Create three main table blocks. 
> Table 1: 'USER' with fields id (PK), username, password_hash, token_balance. 
> Table 2: 'TRIP' with fields id (PK), user_id (FK), generated_itinerary, timestamp. 
> Table 3: 'VECTOR_EMBEDDING' with fields embedding_id (PK), user_id (FK), vector_array. 
> Connect USER to TRIP with a 1-to-many relationship line. Connect USER to VECTOR_EMBEDDING with a strict 1-to-1 relationship line."

---

## Note on Figures 7.1, 7.2, 8.1, and 8.2
- **Figures 7.1 & 7.2 (UI Screenshots):** Simply take actual screenshots of your running Next.js application. Eraser cannot generate screenshots of an app!
- **Figures 8.1 & 8.2 (Graphs):** Eraser focuses on architecture. To generate visual performance graphs (Bar charts/Line charts), you should use Python/Matplotlib *or* just ask ChatGPT/Gemini: *"Write me Python code to generate a bar chart showing Task Success Rate (98%, 94%, 88%) vs Query Complexity (Simple, Multi-City, Adversarial) and save it as a PNG."*
