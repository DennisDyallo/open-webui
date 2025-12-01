"""
title: Anthropic Web Search
author: Dennis Dyallo
version: 1.0.0
license: MIT
description: Automatically adds Anthropic's native web search tool to Claude models
required_open_webui_version: 0.3.9
"""

from pydantic import BaseModel, Field
from typing import Optional


class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=0,
            description="Priority level for the filter operations (0-10). Higher priority filters are executed first.",
        )
        enabled: bool = Field(
            default=True,
            description="Enable or disable the web search tool injection",
        )
        max_searches: int = Field(
            default=5,
            description="Maximum number of web searches Claude can perform per request",
            ge=1,
            le=20,
        )
        auto_enable: bool = Field(
            default=True,
            description="Automatically enable web search for all Claude models (claude-*)",
        )

    def __init__(self):
        self.valves = self.Valves()

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """
        Modifies the incoming request to add Anthropic's web search tool for Claude models.
        
        The web search tool is a server-side tool that runs on Anthropic's infrastructure.
        No additional setup or API keys are needed - Claude automatically searches when relevant.
        
        Pricing: $10 per 1,000 searches + standard token costs
        Docs: https://docs.anthropic.com/en/docs/build-with-claude/tool-use/web-search-tool
        """
        if not self.valves.enabled:
            return body

        model = body.get("model", "")
        
        # Check if this is a Claude model (supports: claude-sonnet-4-5, claude-haiku-4-5, claude-opus-4-5, etc.)
        is_claude = any([
            model.startswith("claude-"),
            "claude" in model.lower()
        ])
        
        if not is_claude or not self.valves.auto_enable:
            return body

        # Initialize tools array if it doesn't exist
        if "tools" not in body:
            body["tools"] = []

        # Check if web search tool is already present
        has_web_search = any(
            tool.get("type") == "web_search_20250305" or tool.get("name") == "web_search"
            for tool in body["tools"]
        )

        # Add Anthropic web search tool if not already present
        if not has_web_search:
            web_search_tool = {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": self.valves.max_searches
            }
            body["tools"].append(web_search_tool)
            
            print(f"✅ Anthropic Web Search enabled for {model} (max {self.valves.max_searches} searches)")

        return body

    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """
        Processes the response from the API.
        Logs web search usage for billing tracking.
        """
        if not self.valves.enabled:
            return body

        # Check if web searches were performed
        usage = body.get("usage", {})
        server_tool_use = usage.get("server_tool_use", {})
        web_search_count = server_tool_use.get("web_search_requests", 0)
        
        if web_search_count > 0:
            # Cost calculation: $10 per 1,000 searches
            search_cost = (web_search_count / 1000) * 10
            print(f"🔍 Web searches performed: {web_search_count} (cost: ${search_cost:.4f})")

        return body
