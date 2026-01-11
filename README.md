# MMSummary - Meeting Minutes Summarization Tool

[中文版 (Chinese Version)](./README_ZH.md)

MMSummary is a powerful, full-stack web application designed to automatically summarize long text documents, such as meeting minutes, transcripts, and comprehensive reports. Leveraging the power of Large Language Models (LLMs) and a Map-Reduce strategy, it can process extensive content that exceeds typical token limits, delivering concise and accurate summaries.

![MMSummary Home](./jpg/home.png)

## Key Features

*   **Intelligent Text Summarization**:
    *   **Map-Reduce Architecture**: Effectively handles large documents by splitting them into manageable chunks ("Map" phase) and then synthesizing the results ("Reduce" phase).
    *   **Customizable Strategies**: Configure chunk sizes, overlaps, and token limits to fine-tune the summarization process for different document types.
    *   **Model Flexibility**: Support for various LLMs via OpenRouter and OpenAI (e.g., Google Gemma, GPT-4o).
*   **Custom Prompt Templates**:
    *   Full control over the summarization output by customizing the "Map" (chunk summary) and "Reduce" (final synthesis) prompts.
    *   Adjust `temperature` to control the creativity/determinism of the model.
*   **History & Persistence**:
    *   Automatically saves all summarization results to a MongoDB database.
    *   View, track, and delete past summaries, complete with processing metrics.
*   **Modern User Interface**:
    *   Clean, responsive frontend built with **React** and **Material-UI**.
    *   Easy file upload setup for `.txt` and `.md` files.
    *   Dedicated settings page for granular control over the AI parameters.

## Technology Stack

### Backend
*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) - High-performance web framework for building APIs.
*   **AI Orchestration**: [LangChain](https://python.langchain.com/) - Framework for developing applications powered by language models.
*   **Database**: [MongoDB](https://www.mongodb.com/) - NoSQL database for flexible data storage.
*   **Runtime**: Python 3.x

### Frontend
*   **Framework**: [React](https://react.dev/) (via [Vite](https://vitejs.dev/))
*   **UI Library**: [Material-UI (MUI)](https://mui.com/) - Comprehensive suite of UI tools.
*   **Routing**: React Router
*   **HTTP Client**: Axios

## Project Structure

```
MMSummary/
├── backend/            # FastAPI application
│   ├── api.py          # API endpoints and route logic
│   ├── core.py         # Core summarization logic (LangChain integration)
│   ├── database.py     # MongoDB connection and CRUD operations
│   └── schemas.py      # Pydantic models for request/response validation
├── frontend/           # React application
│   ├── src/
│   │   ├── components/ # Reusable UI components (InputSection, ResultSection)
│   │   ├── pages/      # Page components (SettingsSection, HistoryPage)
│   │   └── App.jsx     # Main application layout and state
├── template/           # Default prompt templates for Map/Reduce
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

## Getting Started

### Prerequisites
*   Node.js (v16+)
*   Python (v3.8+)
*   MongoDB (Running locally or accessible via URL)

### 1. Backend Setup

1.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

2.  Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Configure environment variables:
    Create a `.env` file in the root directory and add your API keys:
    ```env
    OPENAI_API_KEY=your_openai_key
    OPENROUTER_API_KEY=your_openrouter_key
    MONGODB_URL=mongodb://localhost:27017
    ```

4.  Start the Backend Server:
    ```bash
    python -m backend.api
    ```
    The API will be available at `http://localhost:8000` (or `8001` depending on config).

### 2. Frontend Setup

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```

2.  Install Javascript dependencies:
    ```bash
    npm install
    ```

3.  Start the Development Server:
    ```bash
    npm run dev
    ```
    Access the web interface typically at `http://localhost:5173`.

## Usage Guide

1.  **Home / Summarize**:
    *   Upload a text file or paste text directly.
    *   Click "Start Summarize" to process the text.
2.  **Settings**:
    *   Navigate to the "Settings" tab to adjust Model type, Token limits, Chunk sizes, and Custom Prompts.
    *   Enable "Test Mode" to verify the flow without consuming API credits.
3.  **History**:
    *   View previously generated summaries in the "History" tab.


