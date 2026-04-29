"""MCP Server — Tool registry and dispatcher for DataPilot AI."""

import json
from tools.csv_loader import load_csv
from tools.summarizer import summarize_data
from tools.plotter import plot_distribution
from tools.top_n import top_n_values
from tools.filter_tool import filter_data
from tools.data_cleaner import clean_data
from tools.join_datasets import join_data
from tools.forecast_trends import forecast_trends


class MCPServer:
    """
    Model Context Protocol server that manages tool registration,
    schema generation, and tool dispatch for the DataPilot agent.
    """

    def __init__(self):
        # Registry: map tool name → callable
        self.tool_registry: dict = {
            "load_csv": load_csv,
            "summarize_data": summarize_data,
            "plot_distribution": plot_distribution,
            "top_n_values": top_n_values,
            "filter_data": filter_data,
            "clean_data": clean_data,
            "join_data": join_data,
            "forecast_trends": forecast_trends,
        }

        # Tool schemas in Anthropic tool-use format
        self._tool_schemas: dict = {
            "load_csv": {
                "name": "load_csv",
                "description": (
                    "Load a CSV file and return its schema information including column names, "
                    "data types, row count, a 5-row preview, and missing value counts. "
                    "Always call this first to understand the dataset structure."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "The uploaded CSV filename",
                        }
                    },
                    "required": ["filename"],
                },
            },
            "summarize_data": {
                "name": "summarize_data",
                "description": (
                    "Compute comprehensive summary statistics for the dataset: "
                    "descriptive stats for numeric columns (mean, std, min, max, quartiles), "
                    "value counts for categorical columns (top 10), null percentages, "
                    "duplicate row count, and memory usage. Use this for 'summarize', "
                    "'describe', or 'overview' questions."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "The uploaded CSV filename",
                        },
                        "columns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of specific columns to summarize. If omitted, all columns are summarized.",
                        },
                    },
                    "required": ["filename"],
                },
            },
            "plot_distribution": {
                "name": "plot_distribution",
                "description": (
                    "Generate an interactive distribution chart for a given column using Plotly. "
                    "For numeric columns, produces a histogram. "
                    "For categorical columns, produces a horizontal bar chart of top values. "
                    "Use this for 'show distribution', 'plot', 'chart', or 'visualize' questions."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "The uploaded CSV filename",
                        },
                        "column": {
                            "type": "string",
                            "description": "Column name to plot",
                        },
                        "chart_type": {
                            "type": "string",
                            "enum": ["auto", "histogram", "bar"],
                            "description": "Chart type. 'auto' will detect based on column data type.",
                            "default": "auto",
                        },
                    },
                    "required": ["filename", "column"],
                },
            },
            "top_n_values": {
                "name": "top_n_values",
                "description": (
                    "Find the top N values in a column by count, sum, mean, max, or min. "
                    "Use this to answer questions like 'what are the top-selling products', "
                    "'which region has highest revenue', 'most common categories', or 'highest speed'. "
                    "Results are also exported as a downloadable CSV."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "The uploaded CSV filename",
                        },
                        "column": {
                            "type": "string",
                            "description": "Column name to analyze",
                        },
                        "n": {
                            "type": "integer",
                            "description": "Number of top results to return",
                            "default": 10,
                        },
                        "metric": {
                            "type": "string",
                            "enum": ["count", "sum", "mean", "max", "min"],
                            "description": "Aggregation method",
                        },
                    },
                    "required": ["filename", "column"],
                },
            },
            "filter_data": {
                "name": "filter_data",
                "description": (
                    "Filter rows in the CSV by a column condition. "
                    "Supports operators: eq (equals), gt (greater than), lt (less than), "
                    "gte (>=), lte (<=), contains (substring match). "
                    "Returns the count of matching rows, a 10-row preview, and an export URL for downloading the filtered data."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "The uploaded CSV filename",
                        },
                        "column": {
                            "type": "string",
                            "description": "Column name to filter on",
                        },
                        "operator": {
                            "type": "string",
                            "enum": ["eq", "gt", "lt", "gte", "lte", "contains"],
                            "description": "Comparison operator",
                        },
                        "value": {
                            "type": "string",
                            "description": "The value to compare against",
                        },
                    },
                    "required": ["filename", "column", "operator", "value"],
                },
            },
            "clean_data": {
                "name": "clean_data",
                "description": (
                    "Clean a CSV dataset automatically. Performs operations like: "
                    "drop_duplicates (remove duplicate rows), fill_nulls (fill missing values with median/mode), "
                    "drop_nulls (remove rows with missing data), fix_dates (convert date strings to proper format), "
                    "strip_whitespace (trim spaces from text). Use 'auto' for all safe cleaning operations. "
                    "Saves the cleaned file as a new CSV."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "The uploaded CSV filename to clean",
                        },
                        "operations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of cleaning operations: 'auto', 'drop_duplicates', 'fill_nulls', 'drop_nulls', 'fix_dates', 'strip_whitespace'",
                            "default": ["auto"],
                        },
                    },
                    "required": ["filename"],
                },
            },
            "join_data": {
                "name": "join_data",
                "description": (
                    "Join/merge two CSV datasets on a common column. "
                    "Supports inner, left, right, and outer joins. "
                    "The merged result is saved as a new CSV file that can be used for further analysis. "
                    "Use this when the user wants to combine, merge, or join two datasets."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file1": {
                            "type": "string",
                            "description": "Name of the first CSV file",
                        },
                        "file2": {
                            "type": "string",
                            "description": "Name of the second CSV file",
                        },
                        "join_column": {
                            "type": "string",
                            "description": "Column name to join on (must exist in both files)",
                        },
                        "join_type": {
                            "type": "string",
                            "enum": ["inner", "left", "right", "outer"],
                            "description": "Type of SQL-style join to perform",
                            "default": "inner",
                        },
                    },
                    "required": ["file1", "file2", "join_column"],
                },
            },
            "forecast_trends": {
                "name": "forecast_trends",
                "description": (
                    "Forecast future trends for a numeric column based on historical date-value data. "
                    "Uses polynomial regression to predict future values and generates an interactive chart "
                    "showing historical data, trend line, and forecast. "
                    "Use this for 'predict', 'forecast', 'future trends', or 'what will happen' questions. "
                    "Requires a date column and a numeric value column."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "The uploaded CSV filename",
                        },
                        "date_column": {
                            "type": "string",
                            "description": "Column containing date/time values",
                        },
                        "value_column": {
                            "type": "string",
                            "description": "Numeric column to forecast",
                        },
                        "periods": {
                            "type": "integer",
                            "description": "Number of future days to predict",
                            "default": 30,
                        },
                        "aggregation": {
                            "type": "string",
                            "enum": ["sum", "mean", "count"],
                            "description": "How to aggregate daily data",
                            "default": "sum",
                        },
                    },
                    "required": ["filename", "date_column", "value_column"],
                },
            },
        }

    def get_tool_definitions(self) -> list[dict]:
        """Return all tool schemas for the LLM API call."""
        return list(self._tool_schemas.values())

    def get_tool_schema(self, tool_name: str) -> dict | None:
        """Return the schema for a specific tool."""
        return self._tool_schemas.get(tool_name)

    def call_tool(self, tool_name: str, parameters: dict) -> dict:
        """
        Validate and call a registered tool with the given parameters.

        Args:
            tool_name: Name of the tool to call.
            parameters: Dictionary of parameters to pass to the tool.

        Returns:
            Result dictionary from the tool, or an error dict.
        """
        if tool_name not in self.tool_registry:
            return {"error": f"Unknown tool '{tool_name}'. Available tools: {list(self.tool_registry.keys())}"}

        tool_fn = self.tool_registry[tool_name]

        # Validate required parameters
        schema = self._tool_schemas.get(tool_name, {})
        required = schema.get("input_schema", {}).get("required", [])
        for req_param in required:
            if req_param not in parameters:
                return {"error": f"Missing required parameter '{req_param}' for tool '{tool_name}'."}

        try:
            print(f"  [TOOL] Calling tool: {tool_name}({json.dumps(parameters, default=str)[:200]})")
            result = tool_fn(**parameters)
            print(f"  [OK] Tool '{tool_name}' returned successfully")
            return result
        except TypeError as e:
            return {"error": f"Invalid parameters for tool '{tool_name}': {str(e)}"}
        except Exception as e:
            return {"error": f"Tool '{tool_name}' failed: {str(e)}"}
