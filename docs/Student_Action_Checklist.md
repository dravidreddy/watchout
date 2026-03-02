# Watchout Project Report - Student Action Checklist

This checklist details the explicit tasks you (the student) need to complete to finalize the `Watchout_Comprehensive_Report.md` before converting it to a PDF for your college submission.

## 🖼️ Part 1: Figures & Diagrams You Need to Create

To make the report look professional and hit the 75+ page requirement, you need to generate/capture the following 13 figures and insert them where the `[PLACEHOLDER]` tags are located in the report.

### Conceptual & Architecture Diagrams (Use Draw.io, Lucidchart, or Canva)
- [ ] **Figure 1.1: Watchout High-Level Conceptual Workflow** 
  - *Idea:* A simple block flowchart showing: `User Query -> Next.js UI -> FastAPI Backend -> LLM/Agents -> External APIs`.
- [ ] **Figure 3.1: User Query Processing vs. Monolithic LLMs** 
  - *Idea:* A diagram showing a single ChatGPT box getting confused by 6 APIs vs. your decentralized Agent boxes.
- [ ] **Figure 4.1: Watchout N-Tier System Architecture** 
  - *Idea:* A standard 3-layer architecture diagram (Frontend Layer, API Server Layer, AI/Database Layer).
- [ ] **Figure 4.2: Decentralized Multi-Agent Architecture using LangGraph** 
  - *Idea:* A node-based diagram showing the Orchestrator delegating to specialized agents (Flights, Hotels, Transit).
- [ ] **Figure 4.3: Model Context Protocol (MCP) Integration Paradigm** 
  - *Idea:* Show the "MCP Server" acting as a translation bridge between the Agent (Client) and the Amadeus/Skyscanner API.

### UML Diagrams (Standard College Requirement)
- [ ] **Figure 4.4: Data Flow Diagram (DFD) - Level 0** 
  - *Idea:* A high-level circle representing the system, with user inputs ("trip constraints") going in, and outputs ("itinerary") coming out.
- [ ] **Figure 4.5: Data Flow Diagram (DFD) - Level 1** 
  - *Idea:* A breakdown of Level 0 into distinct sub-processes (Parsing, Vector Retrieval, API Fetching, Assembly).
- [ ] **Figure 4.6: Use Case Diagram for User Interactions** 
  - *Idea:* Stick figures mapping to ovals (e.g., User -> "Input Constraints", "View Itinerary", "Link Instagram").
- [ ] **Figure 4.7: Sequence Diagram** 
  - *Idea:* A vertical timeline diagram (Client -> FastAPI -> LangGraph -> MCP -> Output).

### Database & Flow Logic
- [ ] **Figure 5.1: E-R Diagram for MongoDB and Vector Memory** 
  - *Idea:* Show the `Users` table connecting to the `Trips` table and `ChromaDB Embeddings`.
- [ ] **Figure 6.1: LangGraph Edge/Node Transition State Machine** 
  - *Idea:* You can actually generate this directly from LangGraph using `app.get_graph().draw_mermaid()`, or draw a state machine flowchart.
- [ ] **Figure 7.3: Instagram OAuth Flow** 
  - *Idea:* A simple flowchart showing Frontend -> Meta API -> Token -> Backend -> DB.

### Application Screenshots (Capture these from your running app)
- [ ] **Figure 7.1: User Interface - Landing Page** 
  - *Action:* Take a sleek screenshot of your Next.js homepage.
- [ ] **Figure 7.2: User Interface - Chat Stream** 
  - *Action:* Take a screenshot of the chat interface showing a generated itinerary or the system "thinking" (SSE streaming).

### Data & Results (Use Excel or Chart.js)
- [ ] **Figure 8.1: Task Success Rate vs. Complexity** 
  - *Idea:* A bar graph showing basic queries at 98% success and complex queries at 88%.
- [ ] **Figure 8.2: Latency vs. Node Execution Time** 
  - *Idea:* A line graph showing how long it takes to plan a 1-day trip vs. a 5-day trip.

---

## 📝 Part 2: Final Formatting & Administrative Tasks

Once you have created the images above, follow these steps:

1. **Insert Images:** Replace the text `[PLACEHOLDER: Add Figure X.X: ...]` in the markdown file with standard markdown image links: `![Figure X.X Title](./images/your_image.png)`.
2. **Update Signatures:** Go to the `DECLARATION` and `CERTIFICATE` sections at the very top of the `.md` file and ensure the formatting looks correct for where you and your professor need to physically sign.
3. **Verify Page Breaks:** The report uses `<div style="page-break-after: always;"></div>` to force new pages. When you convert this markdown to PDF (using a tool like pandoc, VS Code Markdown PDF extension, or an online converter), double-check that chapters start on fresh pages.
4. **Final Proofread For Typos:** Read through the *Implementation Details* (Chapter 5 & 6) to ensure the code snippets I provided exactly match how your specific `app.main` or `agents.py` is written. If you renamed an agent, update the text!
5. **Convert to PDF:** Export `Watchout_Comprehensive_Report.md` to a professional PDF format for your final submission.
