# ChatGPT Prompts for Generating Report Images

If you do not want to use Python to generate your performance graphs, or if you don't want to take manual screenshots of your application UI, you can use **ChatGPT Plus (which includes DALL-E 3 and Advanced Data Analysis)** to generate the exact image files for you.

Copy and paste the following prompts directly into ChatGPT.

---

## 1. Figure 8.1: Task Success Rate vs. Complexity (Bar Chart)
*(Note: ChatGPT will use its Advanced Data Analysis python environment to accurately plot this chart for you to download as a PNG).*

**Prompt for ChatGPT:**
> "I need a highly professional, dark-themed, academic-style bar chart generated using Python (matplotlib/seaborn). 
> The title should be: 'Figure 8.1: Task Success Rate vs. Query Complexity'.
> X-axis label: 'Query Complexity'. Categories along the X-axis: ['Simple Route', 'Multi-City', 'Strict Budget Constraints', 'Adversarial/Impossible'].
> Y-axis label: 'Task Success Rate (%)'. Set the Y-axis limit from 0 to 100.
> The data points corresponding to the categories are: [98.7, 94.2, 88.0, 100.0].
> Make the bars a sleek, modern neon blue on a dark gray background. Add the exact percentage number on top of each bar. Return the final chart to me as a high-resolution PNG file that I can download."

---

## 2. Figure 8.2: Latency vs. Node Execution Time (Line Chart)
*(Note: ChatGPT will use its Advanced Data Analysis python environment to accurately plot this chart).*

**Prompt for ChatGPT:**
> "I need a highly professional, dark-themed, academic-style line chart generated using Python. 
> The title should be: 'Figure 8.2: Average Response Latency vs Specialized Agent Execution'.
> X-axis label: 'Number of Specialized Agents Triggered'. Points along the X-axis: [1, 2, 3, 4, 5].
> Y-axis label: 'Average Response Time (seconds)'.
> The data points for the Y-axis are: [3.0, 7.0, 12.5, 18.0, 24.0].
> Plot this as a thick, smooth neon purple line with visible circular markers at each data point. Add a subtle grid to the background. Return the final chart to me as a high-resolution PNG file to download."

---

## 3. Figure 7.1: User Interface - Landing Page
*(Note: ChatGPT will use DALL-E 3 to draw a highly realistic mockup of an AI travel app UI since you aren't providing a real screenshot).*

**Prompt for ChatGPT:**
> "Use DALL-E 3 to generate a highly realistic, high-resolution screenshot of a modern, premium web application landing page viewed on an elegant dark-theme laptop screen. Center the design around an 'AI Travel Planner for India' called 'Watchout'. The UI should feature a sleek, glassmorphism aesthetic with neon gradients (purple and teal). In the center of the UI, show a clean, floating search bar asking 'Where to next?'. Subtle images of Indian landmarks (like Goa beaches or Taj Mahal) should be blurred in the dynamic hero background. Render this to look like a professional SaaS UI mockup."

---

## 4. Figure 7.2: User Interface - Chat Stream with SSE Responses
*(Note: ChatGPT will use DALL-E 3 to draw the chat interface in action).*

**Prompt for ChatGPT:**
> "Use DALL-E 3 to generate a highly realistic, high-resolution screenshot of an AI chat interface specifically designed for an intelligent travel planner called 'Watchout'. The UI should be dark-themed, sleek, and modern (similar to ChatGPT or Claude's interface). On the screen, show a user chat bubble saying 'Plan a 5-day trip to Goa under ₹40,000'. Below it, show the AI agent actively responding with a partially generated itinerary, featuring minimal UI badges that say 'Checking Flights...', 'Validating Hotels...', and 'Grounding via Vectors'. Render it to look like a professional, fully functional frontend React application."
