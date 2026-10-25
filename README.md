Custom GPT ✦ Neo-Brutalist Gemini AI Assistant

A vibrant, feature-rich web interface for interacting with Google Gemini models, built with Python, Streamlit, and LangChain. Features a bold, neo-brutalist UI design, real-time response streaming, customizable assistant personas, and multi-chat session management.

✨ Features

🎨 Neo-Brutalist Design UI: Bold typography, flat palette colors, thick outlines, animated shapes, and hard drop-shadow aesthetics.

⚡ Multiple Gemini Models: Switch seamlessly between gemini-3.5-flash, gemini-3.5-flash-lite, gemini-3.6-flash, gemini-3.7-flash, or bring your own custom Gemini model name.

🎭 Customizable Personas: Toggle between predefined system instructions (e.g., Helpful Assistant, Coding Mentor, Writing Coach, Explain Like I'm Five) or write your own custom system instructions.

💬 Multi-Chat Session Management: Create new chats, switch between conversation histories, and manage individual chat logs.

🔑 Session-Based API Key Handling: Paste your Google AI Studio API key securely—it is stored only in temporary session state and never written to disk or sent to external backends.

🌊 Streaming Responses: Live real-time token streaming with custom CSS typing indicators.

🛠️ Tech Stack

Framework: Streamlit

LLM Integration: LangChain (langchain-google-genai)

AI Model: Google Gemini API

UI & Styling: Custom CSS3 with Google Fonts (Bricolage Grotesque & DM Sans)

🚀 Quick Start

1. Prerequisites

Ensure you have Python 3.9+ installed and a Google Gemini API key.

💡 Get a free API key at Google AI Studio.

2. Installation

Clone this repository and navigate to the project directory:

git clone https://github.com/your-username/custom-gpt-gemini.git
cd custom-gpt-gemini


Create a virtual environment (optional but recommended):

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate


Install the dependencies:

pip install streamlit langchain-google-genai langchain-core


3. Run the Application

Launch the Streamlit app:

streamlit run app.py


Open your browser and navigate to http://localhost:8501.

💻 How to Use

Enter API Key: Paste your Google Gemini API key on the welcome screen and click Start chatting.

Select Persona & Model: Open the sidebar menu (Model and behavior) to choose your preferred AI persona, model version, and temperature setting.

Start Chatting: Use the prompt bar at the bottom to send messages or click one of the quick starter suggestions.

Manage Chats: Use the New chat button in the sidebar to start fresh conversations or delete previous chats using the trash icon.

📂 Project Structure

.
├── app.py              # Main Streamlit application entry point & CSS
├── .streamlit/
│   └── config.toml     # Auto-generated light theme configuration
└── README.md           # Project documentation


🔒 Security & Privacy

API Key Safety: Your Gemini API key is kept solely in memory inside st.session_state during your active session. It is never logged or stored on disk.

No Third-Party Backend: All requests are sent directly from your local application instance to Google's official Gemini API endpoints.
