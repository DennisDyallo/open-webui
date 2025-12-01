# Anthropic Web Search Integration

## Overview

This integration enables Claude models to use **Anthropic's native web search tool** - a server-side capability that runs on Anthropic's infrastructure. No embedding models, no storage requirements, no additional setup needed.

## ✅ Verified Working

We've successfully tested the integration with a direct curl request:

```bash
curl -X POST "https://litellm-proxy-v5wh4bf2aq-uc.a.run.app/v1/chat/completions" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5",
    "messages": [{"role": "user", "content": "What are the latest AI news this week?"}],
    "tools": [{
      "type": "web_search_20250305",
      "name": "web_search",
      "max_uses": 3
    }],
    "max_tokens": 500
  }'
```

**Result:** 
- ✅ Claude automatically searched the web
- ✅ Returned real AI news from late November/early December 2025
- ✅ Included citations with source URLs
- ✅ Usage tracking: `"web_search_requests": 1`
- ✅ No configuration changes needed in LiteLLM

## Architecture

```
User Query → Open WebUI → LiteLLM Proxy → Anthropic API
                                              ↓
                                         Web Search Tool
                                         (Anthropic servers)
                                              ↓
                                         Claude reads results
                                              ↓
                                         Response with citations
```

## Supported Models

All Claude 4.5 models in your deployment support web search:
- ✅ `claude-sonnet-4-5` (claude-sonnet-4-5-20250929)
- ✅ `claude-haiku-4-5` (claude-haiku-4-5-20251001)
- ✅ `claude-opus-4-5` (claude-opus-4-5-20251101)
- ✅ `claude-opus-4-1` (claude-opus-4-1-20250805)

## Pricing

- **$10 per 1,000 searches** + standard token costs
- Each web search = 1 billable search (regardless of results returned)
- Search results content counted as input tokens
- Usage tracked in `usage.server_tool_use.web_search_requests`

## Implementation Options

### Option 1: Custom Open WebUI Function (Recommended)

Use the provided `anthropic_web_search_function.py` to automatically inject the web search tool for all Claude models.

**Installation:**

1. Open Open WebUI admin panel
2. Go to **Workspace → Functions**
3. Click **+ Create New Function**
4. Paste contents of `anthropic_web_search_function.py`
5. Click **Save**

**Features:**
- ✅ Automatically enables web search for all Claude models
- ✅ Configurable max searches per request (default: 5)
- ✅ Cost tracking in server logs
- ✅ Can be toggled on/off per deployment
- ✅ No code changes required

**Configuration (Valves):**
- `enabled`: Enable/disable the function (default: `true`)
- `max_searches`: Max searches per request (default: `5`, range: 1-20)
- `auto_enable`: Auto-enable for Claude models (default: `true`)

### Option 2: Manual GUI Configuration

If Open WebUI supports model-level tool configuration in the GUI:

1. Go to **Workspace → Models**
2. Edit a Claude model (e.g., `claude-sonnet-4-5`)
3. Look for **Tools** or **Advanced Configuration** section
4. Add the web search tool manually:
   ```json
   {
     "type": "web_search_20250305",
     "name": "web_search",
     "max_uses": 5
   }
   ```
5. Save the model configuration

### Option 3: Direct API Calls

If integrating programmatically, include the tool in your API request:

```python
import openai

client = openai.OpenAI(
    base_url="https://litellm-proxy-v5wh4bf2aq-uc.a.run.app/v1",
    api_key="YOUR_LITELLM_MASTER_KEY"
)

response = client.chat.completions.create(
    model="claude-sonnet-4-5",
    messages=[
        {"role": "user", "content": "What are the latest AI developments?"}
    ],
    tools=[{
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": 5
    }]
)
```

## How It Works

1. **User asks a question** that might need current information
2. **Claude evaluates** if web search would be helpful
3. **Anthropic's servers perform the search** (no action required from you)
4. **Results are returned to Claude** with source URLs and snippets
5. **Claude synthesizes an answer** with automatic citations
6. **Response includes** both the answer and citation metadata

## Advanced Configuration

### Domain Filtering

You can restrict or allow specific domains:

```json
{
  "type": "web_search_20250305",
  "name": "web_search",
  "max_uses": 5,
  "allowed_domains": ["example.com", "trusteddomain.org"]
}
```

Or block domains:

```json
{
  "type": "web_search_20250305",
  "name": "web_search",
  "max_uses": 5,
  "blocked_domains": ["untrustedsource.com"]
}
```

### Localization

Localize search results by user location:

```json
{
  "type": "web_search_20250305",
  "name": "web_search",
  "user_location": {
    "type": "approximate",
    "city": "San Francisco",
    "region": "California",
    "country": "US",
    "timezone": "America/Los_Angeles"
  }
}
```

## Response Format

Web search responses include:

```json
{
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Based on the search results, ..."
    },
    {
      "type": "text",
      "text": "...",
      "citations": [
        {
          "type": "web_search_result_location",
          "url": "https://example.com",
          "title": "Page Title",
          "cited_text": "Relevant excerpt from the page...",
          "encrypted_index": "..."
        }
      ]
    }
  ],
  "usage": {
    "server_tool_use": {
      "web_search_requests": 1
    }
  }
}
```

## Monitoring & Cost Control

### Track Usage

Web search usage appears in the `usage` object:

```python
usage = response.usage
search_count = usage.server_tool_use.get("web_search_requests", 0)
cost = (search_count / 1000) * 10  # $10 per 1,000 searches
print(f"Searches: {search_count}, Cost: ${cost:.4f}")
```

### Set Limits

Use `max_uses` to control costs per request:

```json
{
  "type": "web_search_20250305",
  "name": "web_search",
  "max_uses": 3  // Prevents more than 3 searches per request
}
```

### Organization-Level Controls

Configure domain restrictions in the [Anthropic Console](https://platform.claude.com/settings/privacy) to:
- Whitelist allowed domains across all API requests
- Blacklist prohibited domains
- Set organization-wide policies

## Troubleshooting

### Web search not working

1. **Check model support**: Ensure you're using a supported Claude model
2. **Verify API key**: Confirm `ANTHROPIC_API_KEY` is set correctly
3. **Check logs**: Look for `web_search_requests` in usage metrics
4. **Test directly**: Use the curl example above to bypass Open WebUI

### No citations appearing

- Citations are automatic for web search
- Check the `citations` array in `content` blocks
- Verify you're not stripping metadata from responses

### Rate limits exceeded

Error response will include:
```json
{
  "type": "web_search_tool_result_error",
  "error_code": "too_many_requests"
}
```

Solution: Implement exponential backoff or reduce request frequency

### Cost concerns

- Set lower `max_uses` values (e.g., 2-3 instead of 5)
- Monitor `server_tool_use.web_search_requests` in usage
- Consider caching common queries in your application

## LiteLLM Configuration

The `litellm_config.yaml` has been updated with documentation:

```yaml
model_list:
  # All models support Anthropic's native web search tool (web_search_20250305)
  # To use: Pass tools parameter in API request - LiteLLM will passthrough to Anthropic
  # Pricing: $10 per 1,000 searches + standard token costs
  # Docs: https://docs.anthropic.com/en/docs/build-with-claude/tool-use/web-search-tool
  
  - model_name: claude-sonnet-4-5
    litellm_params:
      model: anthropic/claude-sonnet-4-5-20250929
      api_key: os.environ/ANTHROPIC_API_KEY
```

**No changes needed** - LiteLLM automatically passes tools through to Anthropic.

## Comparison: Anthropic Web Search vs Open WebUI LLM Web Search Tool

| Feature | Anthropic Native | Open WebUI Tool |
|---------|------------------|-----------------|
| **Setup** | None | Install tool, configure embedding models |
| **Storage** | None | ~500MB-1GB for models |
| **Infrastructure** | Anthropic's servers | Your Cloud Run instance |
| **Search Quality** | Anthropic-optimized | DuckDuckGo + embeddings |
| **Citations** | Automatic | Manual implementation |
| **Cold Start** | Instant | Model download time |
| **Cost** | $10/1,000 searches | Free (compute costs only) |
| **VRAM Usage** | None | 500MB-1GB |
| **Reliability** | Anthropic SLA | Your instance uptime |
| **Customization** | Limited | Full control |

**Recommendation:** Use Anthropic's native web search for production deployments. It's simpler, more reliable, and scales better on Cloud Run.

## References

- [Anthropic Web Search Tool Documentation](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/web-search-tool)
- [LiteLLM Anthropic Provider Docs](https://docs.litellm.ai/docs/providers/anthropic)
- [Open WebUI Functions Documentation](https://docs.openwebui.com/features/plugin/functions/)

## License

MIT License - Free to use and modify
