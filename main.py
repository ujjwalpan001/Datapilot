"""DataPilot AI — FastAPI server entry point."""

import os
import pandas as pd
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from models.schemas import AnalyzeRequest, AnalyzeResponse, UploadResponse
from agent import DataPilotAgent
from tools.csv_loader import load_csv
import database as db

load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
CHART_OUTPUT_DIR = os.getenv("CHART_OUTPUT_DIR", "./outputs")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create required directories on startup."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(CHART_OUTPUT_DIR, exist_ok=True)
    os.makedirs("static", exist_ok=True)
    db.init_db()
    print("[START] DataPilot AI server started")
    print(f"   Uploads dir: {os.path.abspath(UPLOAD_DIR)}")
    print(f"   Charts dir:  {os.path.abspath(CHART_OUTPUT_DIR)}")
    yield
    print("[STOP] DataPilot AI server stopped")


app = FastAPI(
    title="DataPilot AI",
    description="Intelligent CSV analysis assistant powered by Groq LLM and MCP tools",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (legacy HTML frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize agent
agent = DataPilotAgent()


# ─── Health Check ───────────────────────────────────────────────
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "2.0", "tools": 8}


# ─── Upload CSV ─────────────────────────────────────────────────
@app.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file for analysis.
    Validates extension and file size, then saves to uploads directory.
    """
    # Validate extension
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    # Read file content
    content = await file.read()

    # Validate size
    file_size_mb = len(content) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File size ({file_size_mb:.1f} MB) exceeds the {MAX_FILE_SIZE_MB} MB limit.",
        )

    # Validate non-empty
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty (0 bytes).")

    # Save file
    filepath = os.path.join(UPLOAD_DIR, file.filename)
    with open(filepath, "wb") as f:
        f.write(content)

    # Validate it's a readable CSV
    csv_info = load_csv(file.filename)
    if not csv_info.get("success"):
        # Clean up invalid file
        os.remove(filepath)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid CSV file: {csv_info.get('error', 'Could not parse the file.')}",
        )

    return UploadResponse(
        filename=file.filename,
        rows=csv_info["rows"],
        columns=csv_info["columns"],
        message=f"Successfully uploaded '{file.filename}' with {csv_info['rows']} rows and {len(csv_info['columns'])} columns.",
    )


# ─── List Uploaded Files ────────────────────────────────────────
@app.get("/files")
async def list_files():
    """List all uploaded CSV files."""
    files = []
    if os.path.exists(UPLOAD_DIR):
        for f in os.listdir(UPLOAD_DIR):
            if f.lower().endswith(".csv"):
                path = os.path.join(UPLOAD_DIR, f)
                size = os.path.getsize(path)
                files.append({"filename": f, "size_bytes": size})
    return {"files": files}


# ─── Analyze ────────────────────────────────────────────────────
@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """
    Analyze uploaded CSV data using natural language queries.
    The LLM agent orchestrates tools to answer the question.
    """
    # Validate file exists
    filepath = os.path.join(UPLOAD_DIR, request.filename)
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=404,
            detail=f"File '{request.filename}' not found. Please upload it first.",
        )

    try:
        result = await agent.analyze(request.query, request.filename)

        # Save messages to session if session_id provided
        if request.session_id:
            db.save_message(request.session_id, "user", request.query)
            db.save_message(
                request.session_id,
                "assistant",
                result.insight,
                chart_url=result.chart_url,
                chart_json=result.chart_json,
                export_url=result.export_url,
                tool_calls=[tc.model_dump() for tc in result.tool_calls_made] if result.tool_calls_made else None,
            )

        return result
    except Exception as e:
        print(f"[ERROR] Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ─── Serve Chart Files ─────────────────────────────────────────
@app.get("/chart/{filename}")
async def get_chart(filename: str):
    """Serve generated chart files (JSON or PNG) from the outputs directory."""
    filepath = os.path.join(CHART_OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Chart '{filename}' not found.")

    if filename.endswith(".json"):
        return FileResponse(filepath, media_type="application/json")
    return FileResponse(filepath, media_type="image/png")


# ─── Export Data Files ──────────────────────────────────────────
@app.get("/export/{filename}")
async def export_data(filename: str):
    """Serve exported CSV data files for download."""
    filepath = os.path.join(CHART_OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Export file '{filename}' not found.")

    return FileResponse(
        filepath,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ─── Column Info ────────────────────────────────────────────────
@app.get("/columns/{filename}")
async def get_columns(filename: str):
    """Return column names and data types for a specific uploaded file."""
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found.")

    try:
        df = pd.read_csv(filepath, nrows=5)
        columns = [
            {"name": col, "dtype": str(dtype)}
            for col, dtype in df.dtypes.items()
        ]
        return {"filename": filename, "columns": columns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read columns: {str(e)}")


# ─── Session Endpoints ─────────────────────────────────────────
@app.post("/sessions")
async def create_session(title: str = "New Session", filename: str = None):
    """Create a new chat session."""
    session = db.create_session(title=title, filename=filename)
    return session


@app.get("/sessions")
async def list_sessions():
    """List all chat sessions."""
    sessions = db.list_sessions()
    return {"sessions": sessions}


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a specific session with its messages."""
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    messages = db.get_session_messages(session_id)
    return {"session": session, "messages": messages}


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its messages."""
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    db.delete_session(session_id)
    return {"message": f"Session '{session_id}' deleted."}


# ─── Serve Frontend ────────────────────────────────────────────
@app.get("/")
async def serve_frontend():
    """Serve the frontend. Tries React build first, falls back to static HTML."""
    react_path = os.path.join("frontend", "dist", "index.html")
    if os.path.exists(react_path):
        return FileResponse(react_path)
    return FileResponse("static/index.html")


# Serve React static assets if they exist
react_dist = os.path.join("frontend", "dist")
if os.path.exists(react_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(react_dist, "assets")), name="react-assets")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
