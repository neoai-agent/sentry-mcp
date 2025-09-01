# Sentry MCP Server

A Model Context Protocol (MCP) server for monitoring and analyzing Sentry metrics, errors, and performance data with intelligent time-based monitoring capabilities.

## Features

- **Intelligent Time-Based Monitoring**: Get issues from any time range (minutes to hours) with automatic optimization
- **Error Monitoring**: Get error rates, trends, and details for Sentry projects
- **Issue Management**: Get issue details, assignments, and status
- **Project Analytics**: Get project statistics and metrics
- **AI-Powered Project Matching**: Uses AI to find the correct project names
- **Context Length Optimization**: Designed to prevent LLM context overflow errors

## Installation

Install directly from GitHub using pipx:

```bash
# Install
pipx install git+https://github.com/neoai-agent/sentry-mcp.git

# Or run without installation
pipx run git+https://github.com/neoai-agent/sentry-mcp.git
```

## Quick Start

### With Sentry API Token
```bash
sentry-mcp --sentry-api-token "YOUR_SENTRY_API_TOKEN" --sentry-org "YOUR_ORGANIZATION" --openai-api-key "YOUR_OPENAI_API_KEY"
```

### With Environment Variables
```bash
export SENTRY_API_TOKEN="your-sentry-api-token"
export SENTRY_ORG="your-organization"
export OPENAI_API_KEY="your-openai-api-key"
sentry-mcp
```

## Available Tools

The Sentry MCP Server provides **4 essential tools** optimized for different monitoring scenarios:

### 1. `get_project_health` 
Get overall project health, statistics, and deployment information for a specific project.

**Usage**: `get_project_health("project_name")`

### 2. `get_recent_issues` ⭐ **Main Tool**
Get recent issues from any time range with intelligent monitoring optimization.

**Parameters**:
- `project_name`: The name of the project to check
- `time_range_minutes`: Time range in minutes (default: 60)

**Time Range Examples**:
- **15 minutes**: `get_recent_issues("healthifyme", 15)` → Real-time monitoring
- **30 minutes**: `get_recent_issues("healthifyme", 30)` → Real-time monitoring  
- **1 hour**: `get_recent_issues("healthifyme", 60)` → Recent monitoring
- **2 hours**: `get_recent_issues("healthifyme", 120)` → Recent monitoring
- **3 hours**: `get_recent_issues("healthifyme", 180)` → Extended monitoring

**Intelligent Monitoring Types**:
| Time Range | Monitoring Type | API Limit | Best For |
|------------|----------------|-----------|----------|
| **1-30 minutes** | `real-time` | 100 issues | Critical alerts, immediate response |
| **31-120 minutes** | `recent` | 75 issues | Regular monitoring, incident response |
| **121+ minutes** | `extended` | 50 issues | Historical analysis, trends |

### 3. `get_issue_analysis`
Get detailed analysis for a specific issue with essential information optimized for LLM context.

**Usage**: `get_issue_analysis("issue_id")`

### 4. `get_issue_trends`
Analyze issue trends and patterns based on hourly and daily statistics.

**Usage**: `get_issue_trends("issue_id")`

## Enhanced Time-Based Monitoring

The `get_recent_issues` tool automatically adapts based on your time requirements:

### **Real-Time Monitoring (1-30 minutes)**
Perfect for critical alerts and immediate incident response:
```python
get_recent_issues("healthifyme", 15)  # Last 15 minutes
get_recent_issues("healthifyme", 30)  # Last 30 minutes
```

### **Recent Monitoring (31-120 minutes)**
Ideal for regular monitoring and incident investigation:
```python
get_recent_issues("healthifyme", 60)   # Last hour
get_recent_issues("healthifyme", 90)   # Last 1.5 hours
get_recent_issues("healthifyme", 120)  # Last 2 hours
```

### **Extended Monitoring (121+ minutes)**
Best for historical analysis and trend identification:
```python
get_recent_issues("healthifyme", 180)  # Last 3 hours
get_recent_issues("healthifyme", 240)  # Last 4 hours
get_recent_issues("healthifyme", 480)  # Last 8 hours
```

## Response Format

### Standard Response Structure
```json
{
  "project_name": "healthifyme",
  "project_slug": "healthifyme",
  "time_range_minutes": 30,
  "time_range_display": "30 minutes",
  "monitoring_type": "real-time",
  "issues_count": 4,
  "issues": [
    {
      "id": "6805913024",
      "shortId": "HEALTHIFYME-ETD",
      "title": "IntegrityError: ...",
      "level": "error",
      "status": "unresolved",
      "lastSeen": "2025-08-21T08:55:37Z",
      "priority": "high",
      "project_name": "healthifyme-etd"
    }
  ]
}
```

## Context Length Optimization

The Sentry MCP Server is specifically designed to prevent `ContextWindowExceededError`:

- **Optimized Field Selection**: Returns only essential issue information
- **Intelligent Limits**: Automatically adjusts API limits based on monitoring type
- **Concise Output**: Focuses on actionable insights rather than raw data
- **Token-Efficient**: Designed to stay within LLM context limits

## Sentry API Permissions

Your Sentry API token needs the following scopes:
- `project:read` - Read project information
- `org:read` - Read organization information
- `event:read` - Read event data
- `member:read` - Read member information

## Configuration

### Environment Variables

You can configure the server using environment variables:

- `SENTRY_API_TOKEN`: Your Sentry API token (required)
- `SENTRY_ORG`: Your Sentry organization slug (required)
- `SENTRY_HOST`: Sentry host URL (default: https://sentry.io)
- `OPENAI_API_KEY`: OpenAI API key for AI-powered features (required)

### Command Line Arguments

- `--sentry-api-token`: Sentry API token
- `--sentry-org`: Sentry organization slug
- `--sentry-host`: Sentry host URL (default: https://sentry.io)
- `--openai-api-key`: OpenAI API key
- `--model`: OpenAI model to use (default: openai/gpt-4o-mini)

## Development

For development setup:
```bash
git clone https://github.com/neoai-agent/sentry-mcp.git
cd sentry-mcp
python -m venv sentry-venv
source sentry-venv/bin/activate  # On Windows: sentry-venv\Scripts\activate
pip install -e .
```

## Troubleshooting

### Common Issues

1. **"No issues found" when UI shows issues**: Check project name matching and time range
2. **Context window exceeded**: The tools are optimized to prevent this - check your LLM's context limit
3. **Project not found**: Ensure the project name matches exactly or use AI-powered matching

### Debug Logging

The server includes comprehensive debug logging to help diagnose issues:
- Project matching process
- API response formats
- Time filtering results
- Issue processing details

## License

MIT License - See [LICENSE](LICENSE) file for details
