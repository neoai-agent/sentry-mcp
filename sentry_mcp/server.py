from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import logging
from mcp.server.fastmcp import FastMCP
from sentry_mcp.client import SentryClient, SentryClientConfig
import traceback

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('sentry_mcp')


class SentryMCPServer:
    def __init__(self, model: str, openai_api_key: str, sentry_config: SentryClientConfig):
        self.mcp = FastMCP("sentry-mcp")
        self.client = SentryClient(config=sentry_config, model=model, openai_api_key=openai_api_key)
        self._register_tools()

    def _register_tools(self):
        """Register essential MCP tools with the Sentry MCP server"""
        self.mcp.tool()(self.get_project_health)
        self.mcp.tool()(self.get_recent_issues)
        self.mcp.tool()(self.get_issue_analysis)
        self.mcp.tool()(self.get_issue_trends)

    def run_mcp_blocking(self):
        """
        Runs the FastMCP server. This method is blocking and should be called
        after any necessary asynchronous initialization has been completed.
        """
        self.mcp.run(transport='stdio')

    async def get_project_health(self, project_name: str):
        """Get overall project health and latest release
        Args:
            project_name: The name of the project to check
        Returns:
            A dictionary containing essential project health information
        """
        try:
            matches = await self.client.find_matching_project(project_name=project_name)
            if "error" in matches:
                return matches
            
            project_slug = matches["project_slug"]
            project_display_name = matches["project_name"]
            
            project_details = self.client.get_project_details(project_slug=project_slug)
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=24)
            
            essential_details = {
                "status": project_details.get("status", "unknown"),
                "platform": project_details.get("platform", "unknown"),
                "dateCreated": project_details.get("dateCreated", "unknown"),
                "latestRelease": project_details.get("latestRelease", "unknown")
            }
            
            recent_issues = self.client.get_project_issues(
                project_slug=project_slug,
                since=self.client.datetime_to_timestamp(start_time),
                until=self.client.datetime_to_timestamp(end_time)
            )
            
            issues_count = 0
            if isinstance(recent_issues, dict) and 'data' in recent_issues:
                issues_count = len(recent_issues['data'])
            elif isinstance(recent_issues, list):
                issues_count = len(recent_issues)
            
            return {
                "project_name": project_display_name,
                "project_slug": project_slug,
                "health_status": essential_details["status"],
                "platform": essential_details["platform"],
                "latestRelease": essential_details["latestRelease"],
                "recent_issues_count": issues_count,
            }
        except Exception as e:
            logger.error(f"Error getting project health: {e}")
            return {"error": f"Failed to get project health: {str(e)}"}

    async def get_recent_issues(self, project_name: str, time_range_minutes: int = 60):
        """Get recent issues for a project within specified time range
        Args:
            project_name: The name of the project to check
            time_range_minutes: Time range in minutes to get data for (default: 60 = 1 hour)
                              - For real-time monitoring: 1-30 minutes
                              - For recent monitoring: 31-120 minutes
                              - For extended monitoring: 121+ minutes
        Returns:
            A dictionary containing recent issues and monitoring information
        """
        try:
            logger.info(f"Looking for project: {project_name}")
            
            matches = await self.client.find_matching_project(project_name=project_name)
            if "error" in matches:
                logger.error(f"Project matching failed: {matches}")
                return matches
            
            project_slug = matches["project_slug"]
            project_display_name = matches["project_name"]
            
            logger.info(f"Found project: {project_display_name} (slug: {project_slug})")

            # Determine monitoring type and settings based on time range
            if time_range_minutes <= 30:
                monitoring_type = "real-time"
                limit = 100
            elif time_range_minutes <= 120:
                monitoring_type = "recent"
                limit = 75
            else:
                monitoring_type = "extended"
                limit = 50

            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=time_range_minutes)
            
            logger.info(f"Time range: {start_time} to {end_time} ({time_range_minutes} minutes) - {monitoring_type} monitoring")
            
            # Get recent issues with appropriate limit
            issues = self.client.get_project_issues(
                project_slug=project_slug, 
                limit=limit,
                since=self.client.datetime_to_timestamp(start_time),
                until=self.client.datetime_to_timestamp(end_time)
            )
            
            if isinstance(issues, dict):
                logger.info(f"API response keys: {list(issues.keys())}")
                if 'data' in issues:
                    logger.info(f"Number of issues returned: {len(issues['data'])}")
                    if issues['data']:
                        logger.info(f"First issue sample: {issues['data'][0]}")
            elif isinstance(issues, list):
                logger.info(f"Number of issues returned: {len(issues)}")
                if issues:
                    logger.info(f"First issue sample: {issues[0]}")
            else:
                logger.warning(f"Unexpected API response format: {issues}")

            recent_issues = []
            
            # Handle both response formats: dict with 'data' key or direct list
            issues_to_process = []
            if isinstance(issues, dict) and 'data' in issues:
                issues_to_process = issues['data']
                logger.info(f"Processing {len(issues_to_process)} issues from dict response for time filtering...")
            elif isinstance(issues, list):
                issues_to_process = issues
                logger.info(f"Processing {len(issues_to_process)} issues from list response for time filtering...")
            else:
                logger.warning(f"Cannot process issues - unexpected format")
                return {"error": f"Unexpected API response format: {type(issues)}"}
            
            for issue in issues_to_process:
                if isinstance(issue, dict):
                    # Check if issue was seen within the requested time range
                    last_seen_str = issue.get('lastSeen')
                    if last_seen_str:
                        try:
                            last_seen_time = datetime.fromisoformat(last_seen_str.replace('Z', '+00:00'))
                            logger.debug(f"Issue {issue.get('shortId')}: lastSeen={last_seen_str}, parsed={last_seen_time}, start_time={start_time}, is_recent={last_seen_time >= start_time}")
                            if last_seen_time >= start_time:
                                recent_issues.append({
                                    "issue_id": issue.get('id'),
                                    "lastSeen": issue.get('lastSeen')
                                })
                        except (ValueError, TypeError):
                            logger.warning(f"Failed to parse lastSeen time for issue {issue.get('id')}: {last_seen_str}")
                            recent_issues.append({
                                    "issue_id": issue.get('id'),
                                    "lastSeen": issue.get('lastSeen')
                            })
            
            if isinstance(issues, dict) and 'data' in issues:
                total_issues = len(issues['data'])
            elif isinstance(issues, list):
                total_issues = len(issues)
            else:
                total_issues = 0
            
            logger.info(f"Final result: {len(recent_issues)} recent issues found out of {total_issues} total issues")
            
            return {
                "project_name": project_display_name,
                "project_slug": project_slug,
                "time_range_minutes": time_range_minutes,
                "time_range_display": f"{time_range_minutes} minutes" if time_range_minutes < 60 else f"{time_range_minutes // 60} hours" if time_range_minutes % 60 == 0 else f"{time_range_minutes // 60}h {time_range_minutes % 60}m",
                "monitoring_type": monitoring_type,
                "issues_count": len(recent_issues),
                "issues": recent_issues
            }
        except Exception as e:
            logger.error(f"Error getting recent issues: {e}")
            return {"error": f"Failed to get recent issues: {str(e)}"}

    async def get_issue_analysis(self, issue_id: str):
        """Get detailed analysis of latest issue in a project
        Args:
            issue_id: The ID of the issue to analyze
        Returns:
            A dictionary containing detailed analysis for the issue
        """
        try:
            issue_details = self.client.get_issue_details(issue_id)
            if "error" in issue_details:
                return issue_details
            
            total_events = self.client.get_issue_events(issue_id, limit=100)
            
            latest_event = self.client.get_issue_latest_event(issue_id)

            error_message = latest_event.get('message', {})
            release_version_of_latest_issue = latest_event.get('release', {}).get('version', {})
            
            analysis = {
                "issue_id": issue_id,
                "shortId": issue_details.get('shortId'),
                "title": issue_details.get('title'),
                "culprit": issue_details.get('culprit'),
                "level": issue_details.get('level'),
                "status": issue_details.get('status'),
                "priority": issue_details.get('priority'),
                "count": issue_details.get('count'),
                "userCount": issue_details.get('userCount'),
                "firstSeen": issue_details.get('firstSeen'),
                "lastSeen": issue_details.get('lastSeen'),
                "assignedTo": issue_details.get('assignedTo'),
                "permalink": issue_details.get('permalink'),
                "metadata": {
                    "filename": issue_details.get('metadata', {}).get('filename'),
                    "function": issue_details.get('metadata', {}).get('function'),
                    "error_type": issue_details.get('metadata', {}).get('type')
                },
                "error_message": error_message,
                "events_count": total_events,
                "release_version_of_latest_issue": release_version_of_latest_issue
            }
            logger.info(f"Issue analysis: {analysis}")
            
            return analysis
        except Exception as e:
            logger.error(f"Error getting issue analysis: {e}")
            return {"error": f"Failed to get issue analysis: {str(e)}"}

    async def get_issue_trends(self, issue_id: str):
        """Get hourly trends and patterns for a specific issue trends in a project
        Args:
            issue_id: The ID of the issue to analyze trends for
        Returns:
            A dictionary containing trend analysis and patterns
        """
        try:
            # Get issue details which includes stats
            issue_details = self.client.get_issue_details(issue_id)
            if "error" in issue_details:
                return issue_details
            
            stats_24h = issue_details.get('stats', {}).get('24h', [])
            stats_30d = issue_details.get('stats', {}).get('30d', [])
            
            # Analyze 24h trends
            if stats_24h:
                total_24h = sum([point[1] for point in stats_24h])
                peak_hour = max(stats_24h, key=lambda x: x[1]) if stats_24h else [0, 0]
                avg_hourly = total_24h / len(stats_24h) if stats_24h else 0
                
                active_hours = [point for point in stats_24h if point[1] > 0]
                
            # Analyze 30d trends
            if stats_30d:
                total_30d = sum([point[1] for point in stats_30d])
                peak_day = max(stats_30d, key=lambda x: x[1]) if stats_30d else [0, 0]
                avg_daily = total_30d / len(stats_30d) if stats_30d else 0
                
                active_days = [point for point in stats_30d if point[1] > 0]
            
            # Convert timestamps to readable format for peak times
            peak_hour_time = datetime.fromtimestamp(peak_hour[0]).strftime('%Y-%m-%d %H:%M:%S') if peak_hour[0] else None
            peak_day_time = datetime.fromtimestamp(peak_day[0]).strftime('%Y-%m-%d') if peak_day[0] else None
            
            trends = {
                "issue_id": issue_id,
                "title": issue_details.get('title'),
                "24h_summary": {
                    "total_events": total_24h,
                    "peak_hour": peak_hour_time,
                    "peak_events": peak_hour[1],
                    "active_hours": len(active_hours)
                },
                "30d_summary": {
                    "total_events": total_30d,
                    "peak_day": peak_day_time,
                    "peak_events": peak_day[1],
                    "active_days": len(active_days)
                }
            }
            
            return trends
        except Exception as e:
            logger.error(f"Error getting issue trends: {e}")
            return {"error": f"Failed to get issue trends: {str(e)}"}

