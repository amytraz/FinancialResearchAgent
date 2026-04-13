import json
import os
from typing import Dict, Any, Callable

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, name: str, func: Callable, schema_path: str):
        """Registers a tool with its implementation and metadata schema[cite: 131, 138]."""
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        self.tools[name] = {
            "function": func,
            "schema": schema,
            "description": schema.get("description", "")
        }

    def get_all_schemas(self):
        """Returns schemas to be injected into the System Prompt[cite: 155, 455]."""
        return [tool["schema"] for tool in self.tools.values()]

    def execute(self, name: str, params: Dict[str, Any]):
        """Executes the tool with provided parameters[cite: 138]."""
        if name not in self.tools:
            return f"Error: Tool '{name}' not found."
        return self.tools[name]["function"](**params)