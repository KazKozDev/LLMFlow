"""
ChainOrchestrator module for managing sequential or conditional chains of tool executions.
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass

@dataclass
class ChainStep:
    """Data structure representing a step in a tool execution chain."""
    tool_name: str
    function_name: str
    input_params: Dict[str, Any]
    output_key: str
    condition: Optional[str] = None

class ChainOrchestrator:
    """Manages sequential or conditional chains of tool executions."""
    
    def __init__(self, agent):
        """
        Initialize the ChainOrchestrator.
        
        Args:
            agent: Reference to LLMFlowAgent for accessing LLM and tools
        """
        self.agent = agent
        self.memory = agent.memory
        self.tool_registry = self._build_tool_registry()
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def _build_tool_registry(self) -> Dict[str, Dict[str, Callable]]:
        """Build a registry mapping tool names to their callable functions."""
        registry = {}
        for tool_name, tool_info in self.agent.tools.items():
            registry[tool_name] = {}
            for func_name, func in tool_info.get("functions", {}).items():
                registry[tool_name][func_name] = func
        return registry

    def define_chain(self, chain_config: Union[List[Dict], str]) -> List[ChainStep]:
        """
        Define a chain from configuration.
        
        Args:
            chain_config: List of ChainStep dicts or JSON/YAML string
            
        Returns:
            List[ChainStep]: Validated chain of steps
        """
        if isinstance(chain_config, str):
            chain_config = json.loads(chain_config)
            
        chain = []
        for step_config in chain_config:
            # Validate tool and function exist
            tool_name = step_config["tool_name"]
            function_name = step_config["function_name"]
            if tool_name not in self.tool_registry or function_name not in self.tool_registry[tool_name]:
                raise ValueError(f"Invalid tool or function: {tool_name}.{function_name}")
                
            chain.append(ChainStep(
                tool_name=tool_name,
                function_name=function_name,
                input_params=step_config["input_params"],
                output_key=step_config["output_key"],
                condition=step_config.get("condition")
            ))
        return chain

    def generate_chain(self, query: str) -> List[ChainStep]:
        """
        Generate a chain of tool calls based on the query.
        
        Args:
            query: User's query
            
        Returns:
            List[ChainStep]: Generated chain of steps
        """
        # Create tool descriptions for the LLM
        tool_descriptions = []
        for tool_name, tool_info in self.agent.tools.items():
            tool_desc = {
                "name": tool_name,
                "description": tool_info.get("description", ""),
                "functions": list(self.tool_registry[tool_name].keys())
            }
            tool_descriptions.append(tool_desc)
            
        prompt = f"""Given the query: "{query}"
Available tools: {json.dumps(tool_descriptions, indent=2)}

Generate a chain of tool calls to answer the query. Each step should specify:
- tool_name
- function_name
- input_params (use placeholders like {{previous_output.weather_data}} for dependencies)
- output_key
- condition (optional, for conditional execution)

IMPORTANT: You must respond with ONLY a valid JSON array. Example:
[
    {{"tool_name": "weather_tool", "function_name": "get_weather", "input_params": {{"location": "Tokyo"}}, "output_key": "weather_data"}},
    {{"tool_name": "news_tool", "function_name": "search_news", "input_params": {{"query": "{{weather_data.location.city}} events", "max_results": 3}}, "output_key": "news_data", "condition": "weather_data['precipitation']['rain'] > 0"}}
]

Ensure all tool names and functions are valid from the available tools list."""

        # Get chain configuration from LLM
        try:
            llm_response = self.agent.query_llm(prompt)
            llm_response = llm_response.strip()
            
            # Try to find JSON in the response
            json_match = re.search(r'(\[.*\])', llm_response, re.DOTALL)
            if json_match:
                chain_config = json.loads(json_match.group(1))
            else:
                # Try to parse the entire response as JSON
                chain_config = json.loads(llm_response)
                
            if not isinstance(chain_config, list):
                raise ValueError("LLM response is not a valid JSON array")
                
            return self.define_chain(chain_config)
            
        except Exception as e:
            print(f"Error generating chain: {str(e)}")
            print(f"Raw LLM response: {llm_response}")
            # Return an empty chain to trigger the fallback in process_query
            return []

    def _resolve_params(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve parameter placeholders using context values."""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                # Extract path from placeholder
                path = value[2:-2].split(".")
                current = context
                try:
                    for part in path:
                        current = current[part]
                    resolved[key] = current
                except (KeyError, TypeError):
                    raise ValueError(f"Could not resolve placeholder: {value}")
            else:
                resolved[key] = value
        return resolved

    async def _execute_step(self, step: ChainStep, context: Dict[str, Any]) -> Any:
        """Execute a single chain step."""
        # Check cache first
        cache_key = f"{step.tool_name}.{step.function_name}.{json.dumps(step.input_params)}"
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if (datetime.now() - cache_entry["timestamp"]).total_seconds() < self.cache_ttl:
                return cache_entry["result"]

        # Resolve input parameters
        resolved_params = self._resolve_params(step.input_params, context)
        
        # Get the tool function
        tool_func = self.tool_registry[step.tool_name][step.function_name]
        
        # Execute with retry for API-based tools
        max_retries = 3
        backoff = 1
        for attempt in range(max_retries):
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, tool_func, *resolved_params.values()
                )
                
                # Cache the result
                self.cache[cache_key] = {
                    "result": result,
                    "timestamp": datetime.now()
                }
                
                return result
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(backoff)
                backoff *= 2

    async def execute_chain(self, chain: List[ChainStep], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a chain of tool calls.
        
        Args:
            chain: List of ChainStep objects
            context: Initial context dictionary
            
        Returns:
            Dict[str, Any]: Final context with all outputs
        """
        context = context or {}
        
        for step in chain:
            # Check condition if present
            if step.condition:
                condition_prompt = f"""Given the context: {json.dumps(context)}
Evaluate the condition: {step.condition}
Return "True" or "False"."""
                
                should_execute = self.agent.query_llm(condition_prompt).strip().lower() == "true"
                if not should_execute:
                    continue
                    
            try:
                result = await self._execute_step(step, context)
                context[step.output_key] = result
                
                # Save to memory
                self.memory.add_tool_usage(
                    tool=step.tool_name,
                    function=step.function_name,
                    args=[str(step.input_params)],
                    result=str(result)
                )
            except Exception as e:
                # Try to get alternative approach from LLM
                error_prompt = f"""Tool {step.tool_name}.{step.function_name} failed with error: {str(e)}
Available tools: {json.dumps(self.agent.tools)}
Suggest an alternative approach or response."""
                
                alternative = self.agent.query_llm(error_prompt)
                context[step.output_key] = {"error": str(e), "alternative": alternative}
                
        return context

    def format_response(self, context: Dict[str, Any]) -> str:
        """Format the chain execution results into a natural language response."""
        prompt = f"""Given the tool outputs: {json.dumps(context)}
Summarize the results in natural language to answer the original query.
Keep the response concise and natural.
Include only relevant information from the context.
If there were any errors, explain them briefly and provide any suggested alternatives."""

        return self.agent.query_llm(prompt)
