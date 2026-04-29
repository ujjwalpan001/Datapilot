# DataPilot AI 📊

**DataPilot is an intelligent CSV analysis assistant powered by a Large Language Model (LLM) and a suite of data analysis tools.**

Simply upload a CSV dataset, ask questions in plain English, and DataPilot will do the rest. It uses the high-speed Groq Llama 3.1 8B model to understand your query, orchestrate the right analytical tools, and deliver instant insights, statistics, and interactive charts. It's like having a data analyst at your fingertips.

---

## How It Works

DataPilot employs an agentic architecture where the LLM acts as the "brain" that decides which "tools" to use to answer a user's question.

1.  **Upload & Query**: The user uploads a CSV file and asks a question (e.g., "What is the distribution of sales by region?").
2.  **Agent Initialization**: The FastAPI backend receives the request and initializes the `DataPilotAgent`. The agent first calls the `load_csv` tool to get the schema (column names and data types) of the dataset.
3.  **LLM Orchestration**: The agent constructs a detailed prompt for the Groq LLM. This prompt includes the user's question, the dataset's schema, and a list of available tools (like `plot_distribution`, `top_n_values`, `filter_data`, etc.).
4.  **Agentic Loop (Tool Use)**:
    *   The LLM analyzes the prompt and decides which tool is best suited to answer the query. It returns a "tool call" to the agent.
    *   The agent executes the specified tool with the parameters provided by the LLM.
    *   The result of the tool (e.g., a JSON object with data, a URL to a generated chart) is sent back to the LLM.
5.  **Synthesize & Respond**: The LLM reviews the tool's output. It may decide to call another tool for deeper analysis or, if it has enough information, synthesize a final, human-readable insight.
6.  **Display Results**: The final text insight, along with any generated charts or data previews, is sent to the frontend and displayed to the user.

This entire process is designed to be fast and seamless, providing a conversational interface for complex data analysis.

---

## Use Cases

DataPilot is versatile and can be used in various scenarios where quick data insights are needed without writing any code:

-   **Business Intelligence**: A sales manager could upload a sales report and ask, "Which products are the top 5 best-sellers in the last quarter?" to quickly identify key performers.
-   **Data Exploration**: A data scientist can get a quick overview of a new dataset by asking, "Summarize this dataset" or "Show me the distribution of each numerical column."
-   **Marketing Analysis**: A marketer could analyze campaign results by asking, "What is the correlation between ad spend and conversions?"
-   **Academic Research**: A researcher could use it to quickly analyze survey data, for instance, by asking, "Plot the age distribution of survey respondents."
-   **Financial Analysis**: An analyst could upload a transaction log and ask, "Filter for all transactions greater than $10,000 and show me the monthly trend."

---

## Features

| Feature | Description |
|---|---|
| 📁 **CSV Upload** | Simple drag-and-drop interface for uploading CSV files. |
| 💬 **Natural Language Queries** | Ask complex questions about your data in plain English. No coding required. |
| 🤖 **Agentic LLM Workflow** | The Groq Llama 3.1 LLM autonomously selects, chains, and executes the right tools to answer your query. |
| 📊 **Automated & Interactive Charts** | Automatically generates interactive charts (histograms, bar charts) using Plotly for visual data exploration. |
| 🔍 **Smart Analysis Tools** | A comprehensive suite of tools for common data analysis tasks: |
| | - **`load_csv`**: Loads and provides a schema and preview of the data. |
| | - **`plot_distribution`**: Visualizes the distribution of a column. |
| | - **`top_n_values`**: Finds the most frequent values in a categorical column. |
| | - **`filter_data`**: Filters the dataset based on user-defined conditions. |
| | - **`clean_data`**: Handles missing or inconsistent data. |
| | - **`forecast_trends`**: Performs time-series forecasting on date-based data. |
| 📤 **Data Export** | Export filtered or cleaned data to a new CSV file. |

---

## Tech Stack

-   **Backend**: **FastAPI** with Uvicorn for the web server.
-   **LLM**: **Groq Llama-3.1-8b-instant** for high-speed reasoning and tool orchestration.
-   **Data Analysis**: **Pandas** and **NumPy** for all data manipulation and analysis tasks.
-   **Charting**: **Plotly** for creating interactive and visually appealing data visualizations.
-   **Schema Validation**: **Pydantic v2** for robust data validation in API requests and responses.
-   **Frontend**: A simple, clean interface built with **HTML**, **CSS**, and **JavaScript**.

---

## Quick Start

### 1. Install Dependencies
```bash
# Navigate to the project directory
cd datapilot

# Install Python packages
pip install -r requirements.txt
```

### 2. Set Your API Key
Create a `.env` file in the root of the project and add your Groq API key:
```
GROQ_API_KEY="gsk_..."
```

### 3. Run the Application
```bash
python main.py
```

Once the server is running, open your web browser and navigate to **http://localhost:8000**.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/upload` | Upload a new CSV file for analysis. |
| `POST` | `/analyze` | Submit a natural language query for a previously uploaded file. |
| `GET` | `/chart/{filename}` | Serves the interactive Plotly chart JSON generated by an analysis. |
| `GET` | `/columns/{filename}` | Retrieves the column names and data types for a file. |
| `GET` | `/health` | A simple health check endpoint. |

---

## Example Queries

Here are a few examples of questions you can ask DataPilot:

-   *"What are the top 10 most common values in the 'category' column?"*
-   *"Show me the distribution of 'total_revenue'."*
-   *"Filter the data to only include rows where 'quantity' is greater than 10."*
-   *"What is the average 'price' for each 'product_type'?"*
-   *"Forecast the sales for the next 12 months based on the 'order_date' column."*
