"""Pydantic request/response schemas for DataPilot AI."""

from pydantic import BaseModel, Field
from typing import Optional


class AnalyzeRequest(BaseModel):
    """Request model for the /analyze endpoint."""
    query: str = Field(..., description="Natural language question about the CSV data")
    filename: str = Field(..., description="Name of the uploaded CSV file")
    top_n: Optional[int] = Field(10, description="Number of top results for ranking queries")
    session_id: Optional[str] = Field(None, description="Session ID for persistent chat history")


class ToolCall(BaseModel):
    """Represents a single tool invocation made by the agent."""
    tool_name: str = Field(..., description="Name of the tool that was called")
    parameters: dict = Field(default_factory=dict, description="Parameters passed to the tool")


class AnalyzeResponse(BaseModel):
    """Response model for the /analyze endpoint."""
    insight: str = Field(..., description="Human-readable analytical insight")
    tool_calls_made: list[ToolCall] = Field(default_factory=list, description="List of tools invoked during analysis")
    chart_url: Optional[str] = Field(None, description="URL to the generated chart, if any")
    chart_json: Optional[str] = Field(None, description="Plotly chart JSON for interactive rendering")
    export_url: Optional[str] = Field(None, description="URL to download exported data, if any")
    data_preview: Optional[dict] = Field(None, description="Preview of data returned by tools")


class UploadResponse(BaseModel):
    """Response model for the /upload endpoint."""
    filename: str = Field(..., description="Saved filename on server")
    rows: int = Field(..., description="Number of rows in the CSV")
    columns: list[str] = Field(default_factory=list, description="Column names")
    message: str = Field(..., description="Status message")
