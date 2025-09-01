# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Intelligent Time-Based Monitoring**: Enhanced `get_recent_issues` tool with automatic monitoring type detection
  - Real-time monitoring (1-30 minutes): 100 issue limit for critical alerts
  - Recent monitoring (31-120 minutes): 75 issue limit for incident response
  - Extended monitoring (121+ minutes): 50 issue limit for historical analysis
- **Granular Time Support**: Support for any minute-based time range (15, 30, 45, 90, 120, etc.)
- **Enhanced Debug Logging**: Comprehensive logging for project matching, API responses, and time filtering
- **Context Length Optimization**: Tools redesigned to prevent LLM context overflow errors
- **Simplified Tool Structure**: Streamlined from 10+ tools to 4 essential, focused tools

### Enhanced
- **`get_recent_issues` Tool**: Now the main monitoring tool with intelligent time range handling
  - Accepts minutes instead of hours for precise control
  - Automatic monitoring type detection based on time range
  - Enhanced response format with monitoring type and display information
  - Better handling of different Sentry API response formats (dict vs list)
- **Project Health Monitoring**: Simplified `get_project_health` for overall project status
- **Issue Analysis**: Optimized `get_issue_analysis` for essential issue information
- **Issue Trends**: Enhanced `get_issue_trends` for pattern analysis

### Removed
- **Deprecated Tools**: Removed complex, context-heavy tools to prevent token limit issues
  - `get_comprehensive_issue_details` (caused context overflow)
  - `get_issues_by_frequency` (redundant functionality)
  - `get_issues_by_user_impact` (redundant functionality)
  - `get_project_performance` (simplified into project health)
  - `get_release_health` (simplified into project health)
  - `get_organization_projects` (simplified into project health)

### Fixed
- **API Response Format Handling**: Fixed handling of both dict and list response formats from Sentry API
- **Time Filtering**: Improved `lastSeen` timestamp parsing and filtering
- **Project Matching**: Enhanced AI-powered project name matching with better logging
- **Context Window Errors**: Eliminated `ContextWindowExceededError` through tool optimization
- **Token Limit Issues**: Reduced tool output size while maintaining essential information

### Technical Details
- **Tool Consolidation**: Streamlined from 10+ tools to 4 essential tools
- **Intelligent Monitoring**: Automatic API limit adjustment based on time range
- **Enhanced Logging**: Comprehensive debug information for troubleshooting
- **Response Format Flexibility**: Handles both Sentry API response formats
- **Time Range Intelligence**: Automatic monitoring type detection and optimization

## [0.1.0] - 2025-08-21

### Added
- Initial release of Sentry MCP server
- Support for Sentry API integration
- Project error monitoring and statistics
- Issue details and management
- AI-powered project name matching
- CLI interface with environment variable support
- Documentation and examples

### Features
- `get_project_health`: Get overall project health and statistics
- `get_recent_issues`: Get recent issues with intelligent time-based monitoring
- `get_issue_analysis`: Get detailed issue analysis optimized for LLM context
- `get_issue_trends`: Analyze issue trends and patterns

### Technical Details
- Built with FastMCP framework
- Supports async/await patterns
- Comprehensive error handling
- Caching for improved performance
- Type hints throughout the codebase
- Modular architecture with separate client and server components
- Enhanced API integration with proper error handling
- Context length optimization to prevent LLM overflow errors
