# DataPilot AI 📊

**Intelligent CSV Analysis Assistant** powered by Groq LLM and MCP tools.

Upload any CSV dataset and ask questions in plain English. DataPilot AI uses the lightning-fast Groq Llama 3.1 8B model to orchestrate analytical tools — delivering instant insights, statistics, and charts.

---

## Quick Start

### 1. Install dependencies
```bash
cd datapilot
pip install -r requirements.txt
```

### 2. Set your API key
Edit `.env` and add your Groq API key:
```
GROQ_API_KEY=gsk_...
```

### 3. Generate sample data
```bash
python generate_data.py
```

### 4. Start the server
```bash
python main.py
```

Open **http://localhost:8000** in your browser.

---

## Features

| Feature | Description |
|---------|-------------|
| 📁 CSV Upload | Drag-and-drop file upload with validation |
| 💬 Natural Language Queries | Ask questions about your data in plain English |
| 📊 Auto-Charts | Automatic histogram/bar chart generation |
| 🔍 Smart Analysis | Top-N, filtering, summaries, and distributions |
| 🤖 Agentic LLM | Groq Llama autonomously selects and chains tools |

## Architecture

```
User Query → FastAPI → Groq Agent → MCP Tool Server → Tools → Results
                                        ↕ (agentic loop)
                                      Groq API
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/upload` | Upload a CSV file |
| `POST` | `/analyze` | Analyze data with a query |
| `GET` | `/chart/{filename}` | Serve generated charts |
| `GET` | `/columns/{filename}` | Get column names/types |
| `GET` | `/health` | Health check |

## Example Queries

- *"What are the top 10 selling products?"*
- *"Summarize this dataset"*
- *"Show me the distribution of total_revenue"*
- *"Which region has the highest average sales?"*
- *"Filter orders where quantity is greater than 10"*

## Tech Stack

- **FastAPI** + Uvicorn
- **Groq Llama-3.1-8b-instant** via Groq SDK
- **Pandas** / **NumPy** for data analysis
- **Matplotlib** / **Seaborn** for charts
- **Pydantic v2** for schemas
