Autonomous Web Search Agent

Zero review project phase 1-2

Student Details: Sanam Dravid Sarath Reddy 

$$2262142$$


Guided By: Dr. Babu Kumar S
Panel: Vinodh Kumar V 

$$2262172$$

, Vaidish T 

$$2262180$$

Institution: CHRIST (DEEMED TO BE UNIVERSITY) BANGALORE INDIA

MISSION: CHRIST is a nurturing ground for an individual's holistic development to make effective contribution to the society in a dynamic environment
VISION: Excellence and Service
CORE VALUES: Faith in God | Moral Uprightness | Love of Fellow Beings | Social Responsibility | Pursuit of Excellence

Agenda

Abstract

Introduction

Why this Project

Problem Statement and Objectives

Literature Review

Software Requirements

References

Abstract

Traditional web search relies on keywords and returns a list of links.

Users must refine queries, filter results, and extract information manually.

This project proposes a conversational, AI-powered web search assistant.

The agent will understand intent, search the web, and summarize content.

It will interact with users through dialogue and ask follow-up questions.

The review explores current research in AI, search, and human-computer interaction to support this vision.

Introduction

Traditional web search is based on keyword input and link lists, placing the burden of finding and understanding information on the user.

Users must manually refine queries, filter irrelevant results, and synthesize content from multiple sources.

This project proposes a conversational, autonomous web search agent that interacts with users in natural language.

The agent will understand user intent, dynamically reformulate queries, retrieve relevant data, and provide synthesized responses.

It aims to collaborate with users by asking clarifying questions and adapting to their needs in real time.

The goal is to create a smarter, more human-like search experience that improves efficiency, accuracy, and engagement.

Why this Project?

Limitations of Traditional Search: Current search engines require users to manually refine queries, sift through links, and interpret information, which can be time-consuming and inefficient.

Rising Need for Intelligent Interaction: With increasing reliance on digital information, users need tools that can understand intent and provide direct, contextual answers.

Advancements in AI: Recent progress in Large Language Models, conversational AI, and memory systems makes it feasible to build intelligent agents that can navigate and interpret web content.

Improved User Experience: A conversational search assistant reduces cognitive load and offers a more natural, intuitive, and engaging way to find information.

Bridging Gaps in Research: The project addresses key gaps in current systems—like lack of adaptability, weak memory integration, and limited collaboration—pushing the boundaries of web-based information retrieval.

Problem Statement

Current web search systems are static and keyword-based, placing a high cognitive load on users. There is a need for an intelligent, conversational agent that can adapt to user intent and assist interactively.

Objectives

Develop an intelligent conversational agent that continuously interprets and adapts to user intent throughout multi-turn interactions.

Design and implement a dynamic retrieval system capable of autonomously reformulating queries and synthesizing web-based information in real time.

Integrate a hybrid memory and dialogue management system to enable context-aware, collaborative human-agent interactions.

Literature Review

| S.No | Year | Title | Authors | Methodology | Research Gaps |
| 1 | 2020 | Conversations with Search Engines: SERP-based Conversational Response Generation | Ren, Chen, Ren, Kanoulas, Monz, de Rijke | Built the Search-as-Conversation dataset and CaSE pipeline using SERP data, with token identification and pointer-generator components. | Limited to SERP-based responses; needs richer multi-turn context handling and real-world evaluation. |
| 2 | 2023 | Ericson: An Interactive Open-Domain Conversational Search Agent | Wang, Ahmadvand, Choi, Karisani, Agichtein | Developed Ericson with QA, IR, intent inference, and dialogue management; evaluated via Alexa Prize real-user conversations. | Memory constraints, intent inference errors, and lack of long-term context continuity. |
| 3 | 2025 | Conversational Intent-Driven GraphRAG: Enhancing Multi-Turn Dialogue Systems... | (CID-GraphRAG team) | Proposed dual-retrieval using intent-transition graphs and semantic search; tested on customer support dialogues, boosting BLEU/ROUGE/METEOR. | Needs adaptation to open-domain web search, multimodality, and broader conversational tasks. |

Software Requirements

Core Frameworks & Libraries

Python 3.8+ - Core programming language

LangChain / Haystack - For chaining LLM-based tools and building the agent

OpenAI/ Hugging Face Transformers - To integrate LLMs like GPT, BERT, or Falcon

Pinecone / FAISS / ChromaDB - For vector similarity search and memory management

Development Tools

Jupyter Notebook / VS Code / PyCharm - For development and experimentation

Git + GitHub / GitLab - For version control

Postman - For testing APIs (optional)

n8n - For automating workflows between search modules, APIs, LLMs, and external services using a visual pipeline editor.

References

S. Brin and L. Page, "The anatomy of a large-scale hypertextual Web search engine," Computer Networks and ISDN Systems, vol. 30, no. 1-7, pp. 107-117, 1998.

L. Gao, A. Madaan, S. Yao, C. S. Wu, and J. Callan, "Rewrite-Retrieve-Read: A Simple and Effective Framework for Query Rewriting in Retrieval-Augmented Large Language Models," arXiv preprint arXiv:2305.14283, 2023.

B. Mitra and N. Craswell, "An Introduction to Neural Information Retrieval," Foundations and Trends in Information Retrieval, vol. 13, no. 1, pp. 1–126, 2018.

Pinecone, "Conversational Memory for LLMs with LangChain." 

$$Online$$

. Available: https://www.pinecone.io/learn/series/langchain/langchain-conversational-memory/. 

$$Accessed: Jul. 9, 2025$$

.

W. Shi, A. Madaan, and S. Yao, "Proactive Conversational AI: A Comprehensive Survey of Advancements and Opportunities," National Science Foundation, 2024.

Smart Travel Agent

Project Review 1

Student Details: Sanam Dravid Sarath Reddy [2262142]
Guided By: Dr. Babu Kumar S
Panel: Vinodh Kumar V [2262172], Vaidish T [2262180]

Institution: CHRIST (DEEMED TO BE UNIVERSITY) BANGALORE INDIA

Agenda

Design & Methodology

Implementation Details

Results & Discussions

Conclusion

Design & Methodology

Core Principle

Our system is built on a decentralized multi-agent architecture, where each agent performs a distinct role.

The Model Context Protocol (MCP) is used as the universal communication backbone for seamless interaction.

MCP enables a structured and verified exchange of data among agents and external APIs.

This design ensures high scalability, interoperability, and long-term adaptability.

Each agent is specialized, ensuring efficiency and reduced overlaps in responsibilities.

The decentralized setup reduces dependency on a single agent, making the system more reliable.

By enforcing tool-based communication, MCP improves accuracy and minimizes hallucinations in responses.

Agent Team & Roles

The Trip Planner Agent (Orchestrator) interprets user requests and delegates tasks to the appropriate agents.

It communicates with other agents strictly through the MCP communication protocol.

The Flights Agent retrieves flight data by exposing tools such as skyscanner.get_flights.

The Hotels Agent provides accommodation options using tools like amadeus.find_hotels and google_places.search.

The Itinerary Agent creates a logical day-to-day travel plan using tools such as Maps.get_travel_time.

The Transport Agent provides real-time ride and transit options using tools like uber.get_ride_estimate and local_transit.get_schedule.

This clear separation of concerns makes the system efficient, modular, and easier to maintain or expand.

Implementation Details

Technical Stack & Orchestration

We use LangGraph to define the workflows between multiple agents.

LangGraph supports both sequential and parallel execution of agent tasks.

Each agent is implemented as either an MCP server or MCP client.

The Python SDK for MCP is used to ensure standardization across all agents.

Popular travel APIs like Skyscanner, Amadeus, and Google Places are integrated by wrapping them in MCP servers.

This approach eliminates the need for custom one-off integrations for each API.

Overall, the system forms a modular, scalable, and future-ready backend.

User Interaction & Memory Management

A Streamlit-based interface serves as the user-facing front end of the system.

When a user submits a request, it is routed to the Trip Planner Agent (Orchestrator).

The Orchestrator then triggers the appropriate MCP-based workflows between specialized agents.

A vector database (FAISS or Pinecone) is used to store contextual information.

Stored memory includes user preferences such as flight classes, destinations, and past itineraries.

This ensures the platform can deliver personalized, context-aware recommendations.

Memory management allows the system to provide continuity across multiple user interactions.

Results and Discussions

Research Findings

Current travel solutions are mostly basic booking platforms or limited chatbots.

None of the existing systems leverage a multi-agent framework with MCP-powered communication.

MCP helps solve the N x M integration problem that has long hindered complex system design.

It allows plug-and-play integration of new APIs and tools without re-architecting the system.

Our evaluation confirms that MCP is a mature, open standard with SDKs available in multiple languages.

MCP also brings strong security benefits, as sensitive data stays within the MCP servers.

Research findings validate MCP as a viable and industry-ready solution for such architectures.

Competitive Advantage

MCP provides a standardized and secure tool-calling framework compared to custom integrations.

By requiring verified queries, MCP prevents hallucinations and ensures real-time data accuracy.

This eliminates the risk of fabricated or incorrect information reaching the user.

While the initial setup of MCP servers requires more effort, it simplifies future development.

Once in place, it reduces the time and cost required to add new features or APIs.

The system is designed to scale easily, supporting rapid expansion into rentals, events, or insurance services.

Altogether, MCP gives the project a unique competitive edge in AI-driven travel solutions.

Conclusion

Key Takeaways

The combination of a multi-agent system with MCP is our project's core strength.

This system goes beyond a simple planner—it represents a new AI architecture model.

The decentralized design ensures robustness, adaptability, and resilience.

MCP standardization provides smooth interoperability across all tools and APIs.

Real-time, tool-based communication guarantees accuracy and trustworthiness.

Our approach makes this the first unified MCP-powered travel assistant.

Overall, the project demonstrates a transformative shift in intelligent travel planning.

Future Outlook

MCP makes the system future-proof and modular, allowing easy upgrades.

New APIs and agents can be integrated without disrupting existing workflows.

The framework ensures accuracy by eliminating hallucinations through verified tools.

Collaboration among specialized agents ensures high efficiency in planning.

Continuous learning and stored memory enable deep personalization for users.

The architecture can scale to serve millions of travelers worldwide.

This project lays the groundwork for the next generation of conversational AI in travel.