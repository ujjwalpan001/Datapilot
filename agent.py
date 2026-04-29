"""DataPilot Agent — Orchestrates Groq LLM with MCP tools for CSV analysis."""

import os
import json
from groq import Groq
from dotenv import load_dotenv
from mcp_server import MCPServer
from models.schemas import AnalyzeResponse, ToolCall

load_dotenv(override=True)

SYSTEM_PROMPT_TEMPLATE = """You are DataPilot AI, an expert business data analyst. The user has uploaded a CSV dataset.

Filename: {filename}

Dataset schema:
{columns_info}

Your job:
- Understand the user's question about the data
- Call the appropriate analysis tools in sequence using the Filename above.
- After receiving tool results, synthesize a clear, actionable insight in 2-4 sentences
- Always start by calling load_csv if you need to understand the data structure
- For "top" questions, use top_n_values with the most relevant column
- For distribution or visual questions, use plot_distribution
- For cleaning or fixing data, use clean_data
- For merging/joining datasets, use join_data
- For prediction/forecast questions, use forecast_trends (requires a date column and value column)
- Mention specific numbers, column names, and values in your response
- Do not make up data - only state what the tools return"""


class DataPilotAgent:
    """
    Core agentic loop: takes a user query, calls Groq with tools,
    processes tool calls iteratively, and returns the final insight.
    """

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        self.client = Groq(api_key=api_key)
        self.mcp_server = MCPServer()
        self.model = "llama-3.1-8b-instant"

    def _build_tools(self) -> list[dict]:
        """Convert MCP tool definitions to Groq/OpenAI function format."""
        tools = []
        for tool_def in self.mcp_server.get_tool_definitions():
            # Clean schema: remove 'default' from properties (not supported)
            schema = tool_def["input_schema"].copy()
            clean_props = {}
            for prop_name, prop_def in schema.get("properties", {}).items():
                clean_prop = {k: v for k, v in prop_def.items() if k != "default"}
                clean_props[prop_name] = clean_prop
            schema["properties"] = clean_props

            tools.append({
                "type": "function",
                "function": {
                    "name": tool_def["name"],
                    "description": tool_def["description"],
                    "parameters": schema,
                }
            })
        return tools

    async def analyze(self, query: str, filename: str) -> AnalyzeResponse:
        """
        Run the full agentic analysis loop.

        1. Load CSV to get schema
        2. Build system prompt with column info
        3. Call Groq with user query + tool definitions
        4. Loop: process tool_calls -> call tools -> feed results back
        5. Return final insight + metadata
        """
        tool_calls_made = []
        chart_url = None
        chart_json = None
        export_url = None
        data_preview = None

        print(f"\n{'='*60}")
        print(f"[ANALYZE] DataPilot Agent - Analyzing: \"{query}\"")
        print(f"[FILE] {filename}")
        print(f"{'='*60}")

        # Step 1: Load CSV to understand the dataset schema
        csv_info = self.mcp_server.call_tool("load_csv", {"filename": filename})
        tool_calls_made.append(ToolCall(tool_name="load_csv", parameters={"filename": filename}))

        if not csv_info.get("success"):
            return AnalyzeResponse(
                insight=f"Failed to load the dataset: {csv_info.get('error', 'Unknown error')}",
                tool_calls_made=tool_calls_made,
            )

        # Capture initial data preview
        if csv_info.get("preview"):
            data_preview = {"preview": csv_info["preview"][:5]}

        # Step 2: Build system prompt with column info
        columns_info = "\n".join(
            f"- {col} ({dtype})" for col, dtype in csv_info.get("dtypes", {}).items()
        )
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(columns_info=columns_info, filename=filename)

        # Step 3: Build tools and initial messages
        groq_tools = self._build_tools()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        print(f"\n[LLM] Calling Groq ({self.model}) with {len(groq_tools)} tools available...")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=groq_tools,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=2048,
        )

        # Step 4: Agentic loop
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            message = response.choices[0].message

            # Check if there are tool calls
            if not message.tool_calls:
                break

            print(f"\n[LOOP] Iteration {iteration}: Groq requested {len(message.tool_calls)} tool call(s)")

            # Append assistant message with tool calls
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            # Process each tool call
            for tc in message.tool_calls:
                tool_name = tc.function.name
                try:
                    tool_input = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    tool_input = {}

                print(f"\n  [CALL] Tool: {tool_name}")
                print(f"     Input: {json.dumps(tool_input, default=str)[:300]}")

                tool_calls_made.append(ToolCall(tool_name=tool_name, parameters=tool_input))

                try:
                    result = self.mcp_server.call_tool(tool_name, tool_input)
                except Exception as e:
                    result = {"error": str(e), "tool": tool_name}

                # Capture chart URL/JSON if generated
                if "chart_url" in result and result.get("chart_url"):
                    chart_url = result["chart_url"]
                if "chart_json" in result and result.get("chart_json"):
                    chart_json = result["chart_json"]

                # Capture export URL if generated
                if "export_url" in result and result.get("export_url"):
                    export_url = result["export_url"]

                # Capture data preview
                if tool_name == "load_csv" and result.get("preview"):
                    data_preview = {"preview": result["preview"][:5]}
                elif tool_name == "filter_data" and result.get("preview"):
                    data_preview = {"filtered_preview": result["preview"]}

                print(f"     Result: {json.dumps(result, default=str)[:300]}")

                # Truncate content to avoid exceeding token limits
                # Remove chart_json from what we send to LLM (it's huge)
                result_for_llm = {k: v for k, v in result.items() if k != "chart_json"}
                content_str = json.dumps(result_for_llm, default=str)
                if len(content_str) > 2500:
                    content_str = content_str[:2500] + "... [TRUNCATED for token limits]"

                # Append tool result as a tool message
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": content_str,
                })

            # Re-call Groq with updated messages
            print(f"\n[LLM] Re-calling Groq with tool results...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=groq_tools,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=2048,
            )

        # Step 5: Extract final text response
        insight = ""
        try:
            final_message = response.choices[0].message
            if final_message.content:
                insight = final_message.content
        except Exception:
            pass

        if not insight.strip():
            insight = (
                "I could not interpret that query. Please try rephrasing "
                "or check that the column name is correct."
            )

        print(f"\n[INSIGHT] {insight[:200]}...")
        print(f"[TOOLS] Total tool calls: {len(tool_calls_made)}")
        print(f"{'='*60}\n")

        return AnalyzeResponse(
            insight=insight,
            tool_calls_made=tool_calls_made,
            chart_url=chart_url,
            chart_json=chart_json,
            export_url=export_url,
            data_preview=data_preview,
        )
