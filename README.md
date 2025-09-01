# Sentry MCP Server

A Model Context Protocol (MCP) server for monitoring Sentry errors and performance data with intelligent time-based monitoring.

## Features

- **Smart Time Monitoring**: Get issues from any time range (minutes to hours) with automatic optimization
- **Error Monitoring**: Track error rates, trends, and details for Sentry projects
- **Issue Management**: Get issue details, assignments, and status
- **AI-Powered Project Matching**: Uses AI to find correct project names
- **Context Optimization**: Designed to prevent LLM context overflow errors

## Quick Installation

```bash
# Install
pipx install git+https://github.com/neoai-agent/sentry-mcp.git

# Or run without installation
pipx run git+https://github.com/neoai-agent/sentry-mcp.git
```

## Quick Start

### Option 1: Command Line
```bash
sentry-mcp --sentry-api-token "YOUR_TOKEN" --sentry-org "YOUR_ORG" --openai-api-key "YOUR_OPENAI_KEY"
```

### Option 2: Environment Variables
```bash
export SENTRY_API_TOKEN="your-token"
export SENTRY_ORG="your-org"
export OPENAI_API_KEY="your-openai-key"
sentry-mcp
```

## Available Tools

### 1. `get_recent_issues` **Main Tool**
Get recent issues with smart time optimization.

**Usage**: `get_recent_issues("project_name", time_minutes)`

**Examples**:
- `get_recent_issues("healthifyme", 15)` - Last 15 minutes (real-time)
- `get_recent_issues("healthifyme", 60)` - Last hour (recent)
- `get_recent_issues("healthifyme", 180)` - Last 3 hours (extended)

### 2. `get_project_health`
Get overall project health and statistics.

**Usage**: `get_project_health("project_name")`

### 3. `get_issue_analysis`
Get detailed analysis for a specific issue.

**Usage**: `get_issue_analysis("issue_id")`

### 4. `get_issue_trends`
Analyze issue trends and patterns.

**Usage**: `get_issue_trends("issue_id")`

## Smart Time Monitoring

The `get_recent_issues` tool automatically adapts based on your time range:

| Time Range | Type | Best For |
|------------|------|----------|
| **1-30 minutes** | Real-time | Critical alerts, immediate response |
| **31-120 minutes** | Recent | Regular monitoring, incident response |
| **121+ minutes** | Extended | Historical analysis, trends |

## Response Format

```json
{
  "project_name": "healthifyme",
  "time_range_minutes": 30,
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
      "priority": "high"
    }
  ]
}
```

## Configuration

### Required Permissions
Your Sentry API token needs: `project:read`, `org:read`, `event:read`, `member:read`

### Environment Variables
- `SENTRY_API_TOKEN`: Your Sentry API token
- `SENTRY_ORG`: Your Sentry organization slug
- `SENTRY_HOST`: Sentry host URL (default: https://sentry.io)
- `OPENAI_API_KEY`: OpenAI API key for AI features

### Command Line Options
- `--sentry-api-token`: Sentry API token
- `--sentry-org`: Sentry organization slug
- `--sentry-host`: Sentry host URL
- `--openai-api-key`: OpenAI API key
- `--model`: OpenAI model (default: openai/gpt-4o-mini)

## Development

```bash
git clone https://github.com/neoai-agent/sentry-mcp.git
cd sentry-mcp
python -m venv sentry-venv
source sentry-venv/bin/activate  # Windows: sentry-venv\Scripts\activate
pip install -e .
```

## Troubleshooting

- **"No issues found"**: Check project name and time range
- **Context window exceeded**: Tools are optimized to prevent this
- **Project not found**: Use exact project name or AI-powered matching

## License

MIT License - See [LICENSE](LICENSE) file for details
