"""
Sentry client implementation for MCP server.
"""

from typing import Dict, List, Any, Optional
import requests
import logging
import json
from datetime import datetime, timezone, timedelta
from litellm import acompletion
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger('sentry_mcp')

@dataclass
class SentryClientConfig:
    api_token: str
    organization: str
    host: str = "https://sentry.io"

class SentryClient:
    """Client for interacting with Sentry API services.
    
    This client handles all interactions with the Sentry API. Note that all timestamp
    parameters (since, until) should be provided as UNIX epoch timestamps (float/int)
    as required by the Sentry API.
    """

    @staticmethod
    def datetime_to_timestamp(dt: datetime) -> int:
        """Convert a datetime object to UNIX epoch timestamp."""
        return int(dt.timestamp())

    def __init__(self, config: SentryClientConfig, model: str, openai_api_key: str):
        """Initialize the Sentry client."""
        self.config = config
        self.model = model
        self.openai_api_key = openai_api_key
        self._name_matching_cache = {}
        self._projects_cache = {
            "data": None,
            "timestamp": None,
            "cache_ttl": 300  # Cache TTL in seconds (5 minutes)
        }
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.config.api_token}',
            'Content-Type': 'application/json'
        })
        self.base_url = f"{self.config.host}/api/0"

    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict:
        """Make a request to the Sentry API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, params=params, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Log the response structure for debugging
            logger.debug(f"API response from {url}: {type(result)} - {str(result)[:200]}...")
            
            # Validate response format
            if result is None:
                logger.warning(f"API returned None for {url}")
                return {}
            
            return result
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Resource not found: {url}. This might indicate the project doesn't exist in organization '{self.config.organization}' or the organization is incorrect.")
            elif e.response.status_code == 400:
                logger.error(f"Bad request: {url}. This might indicate invalid parameters or the project doesn't exist in organization '{self.config.organization}'.")
            else:
                logger.error(f"HTTP error {e.response.status_code}: {url}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse JSON response from {url}: {e}")
            raise

    def get_organization_projects(self) -> List[Dict[str, Any]]:
        """Get all projects in the organization."""
        endpoint = f"/projects/"
        result = self._make_request('GET', endpoint)
        
        # Handle different response formats from Sentry API
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and 'data' in result:
            return result['data']
        else:
            logger.warning(f"Unexpected response format from /projects/ endpoint: {type(result)}")
            return []

    def get_project_details(self, project_slug: str) -> Dict[str, Any]:
        """Get details for a specific project."""
        endpoint = f"/projects/{self.config.organization}/{project_slug}/"
        return self._make_request('GET', endpoint)

    def get_project_stats(self, project_slug: str, stat: str = "received", since: Optional[float] = None, until: Optional[float] = None) -> Dict[str, Any]:
        """Get statistics for a project.
        
        Args:
            project_slug: The project slug
            stat: The statistic type (default: "received")
            since: UNIX epoch timestamp for start time
            until: UNIX epoch timestamp for end time
        """
        endpoint = f"/projects/{self.config.organization}/{project_slug}/stats/"
        params = {'stat': stat}
        if since:
            params['since'] = int(since)  # Convert to integer timestamp
        if until:
            params['until'] = int(until)  # Convert to integer timestamp
        return self._make_request('GET', endpoint, params=params)

    def get_project_events(self, project_slug: str, query: Optional[str] = None, limit: int = 100, since: Optional[float] = None, until: Optional[float] = None) -> Dict[str, Any]:
        """Get events for a project.
        
        Args:
            project_slug: The project slug
            query: Optional query string to filter events
            limit: Maximum number of events to return (default: 100)
            since: UNIX epoch timestamp for start time
            until: UNIX epoch timestamp for end time
        """
        endpoint = f"/projects/{self.config.organization}/{project_slug}/events/"
        params = {'limit': limit}
        if query:
            params['query'] = query
        if since:
            params['since'] = int(since)
        if until:
            params['until'] = int(until)
        return self._make_request('GET', endpoint, params=params)

    def get_project_issues(self, project_slug: str, limit: int = 100, since: Optional[float] = None, until: Optional[float] = None) -> Dict[str, Any]:
        """Get issues for a specific project with optional time filtering."""
        try:
            endpoint = f"/projects/{self.config.organization}/{project_slug}/issues/"
            params = {'limit': limit}
            
            # According to Sentry API docs, statsPeriod can be "24h", "14d", or ""
            # Default to "24h" if not provided
            if since and until:
                time_diff_hours = int((until - since) / 3600)
                if time_diff_hours <= 24:
                    params['statsPeriod'] = '24h'
                elif time_diff_hours <= 336:  # 14 days
                    params['statsPeriod'] = '14d'
                else:
                    params['statsPeriod'] = ''  # No time limit
            else:
                params['statsPeriod'] = '24h'  # Default as per docs
            
            return self._make_request('GET', endpoint, params=params)
        except Exception as e:
            logger.error(f"Failed to get project issues: {e}")
            return {"error": f"Failed to get project issues: {str(e)}"}


    def get_issue_details(self, issue_id: str) -> Dict[str, Any]:
        """Get details for a specific issue."""
        try:
            endpoint = f"/issues/{issue_id}/"
            return self._make_request('GET', endpoint)
        except Exception as e:
            logger.warning(f"Failed to get issue {issue_id} directly: {e}")
            return {"error": f"Failed to get issue details: {str(e)}"}

    def get_issue_latest_event(self, issue_id: str) -> Dict[str, Any]:
        """Get the latest event for a specific issue."""
        try:
            endpoint = f"/issues/{issue_id}/events/latest/"
            return self._make_request('GET', endpoint)
        except Exception as e:
            logger.warning(f"Failed to get latest event for issue {issue_id}: {e}")
            return {"error": f"Failed to get latest event: {str(e)}"}

    def get_issue_events(self, issue_id: str, limit: int = 100) -> Dict[str, Any]:
        """Get events for a specific issue."""
        endpoint = f"/issues/{issue_id}/events/"
        params = {'limit': limit}
        return self._make_request('GET', endpoint, params=params)

    def get_issue_essentials(self, issue_id: str) -> Dict[str, Any]:
        """Get essential issue information in a very concise format."""
        try:
            issue_details = self.get_issue_details(issue_id)
            if "error" in issue_details:
                return issue_details

            result = {
                "issue_id": issue_id,
                "title": issue_details.get("title"),
                "culprit": issue_details.get("culprit"),
                "level": issue_details.get("level"),
                "status": issue_details.get("status"),
                "type": issue_details.get("type"),
                "project": issue_details.get("project", {}).get("slug") if issue_details.get("project") else None,
                "last_seen": issue_details.get("lastSeen"),
                "first_seen": issue_details.get("firstSeen"),
                "total_occurrences": issue_details.get("count"),
                "unique_users_affected": issue_details.get("userCount"),
                "permalink": issue_details.get("permalink")
            }

            try:
                latest_event = self.get_issue_latest_event(issue_id)
                if isinstance(latest_event, dict) and 'message' in latest_event:
                    result["latest_error_message"] = latest_event.get("message")
                    result["platform"] = latest_event.get("platform")
                    result["environment"] = latest_event.get("environment")
                    
                    if 'entries' in latest_event:
                        entries = latest_event['entries']
                        if isinstance(entries, list):
                            for entry in entries:
                                if isinstance(entry, dict) and entry.get('type') == 'user':
                                    user_data = entry.get('data', {})
                                    result["user_info"] = {
                                        "id": user_data.get('id'),
                                        "username": user_data.get('username'),
                                        "ip_address": user_data.get('ip_address')
                                    }
                                    break
            except Exception as e:
                logger.warning(f"Failed to get latest event for issue {issue_id}: {e}")

            return result

        except Exception as e:
            logger.error(f"Failed to get issue essentials: {e}")
            return {"error": f"Failed to get issue essentials: {str(e)}"}

    def get_comprehensive_issue_details(self, issue_id: str) -> Dict[str, Any]:
        """Get comprehensive details for a specific issue including events, user impact, and related data."""
        try:
            issue_details = self.get_issue_details(issue_id)
            if "error" in issue_details:
                return issue_details

            result = {
                "basic_details": {
                    "id": issue_details.get("id"),
                    "shortId": issue_details.get("shortId"),
                    "title": issue_details.get("title"),
                    "culprit": issue_details.get("culprit"),
                    "permalink": issue_details.get("permalink"),
                    "level": issue_details.get("level"),
                    "status": issue_details.get("status"),
                    "type": issue_details.get("type"),
                    "numComments": issue_details.get("numComments"),
                    "assignedTo": issue_details.get("assignedTo"),
                    "project": issue_details.get("project", {}).get("slug") if issue_details.get("project") else None,
                    "lastSeen": issue_details.get("lastSeen"),
                    "firstSeen": issue_details.get("firstSeen"),
                    "count": issue_details.get("count"),
                    "userCount": issue_details.get("userCount")
                },
                "latest_event_summary": {},
                "user_impact_summary": {},
                "available_data": []
            }

            # Get latest event (this endpoint exists: /issues/{issue_id}/events/latest/)
            try:
                latest_event = self.get_issue_latest_event(issue_id)
                if isinstance(latest_event, dict) and 'id' in latest_event:
                    result["latest_event_summary"] = {
                        "event_id": latest_event.get("id"),
                        "message": latest_event.get("message"),
                        "platform": latest_event.get("platform"),
                        "environment": latest_event.get("environment"),
                        "release": latest_event.get("release"),
                        "dist": latest_event.get("dist"),
                        "timestamp": latest_event.get("timestamp"),
                        "size": latest_event.get("size")
                    }
                    result["available_data"].append("latest_event")
                    
                    # Extract user context from the latest event (concise)
                    if 'entries' in latest_event:
                        entries = latest_event['entries']
                        if isinstance(entries, list):
                            user_context = {}
                            for entry in entries:
                                if isinstance(entry, dict) and entry.get('type') == 'user':
                                    user_data = entry.get('data', {})
                                    user_context = {
                                        "id": user_data.get('id'),
                                        "username": user_data.get('username'),
                                        "email": user_data.get('email'),
                                        "ip_address": user_data.get('ip_address')
                                    }
                                    break
                            
                            geo_info = {}
                            if 'contexts' in latest_event:
                                contexts = latest_event['contexts']
                                if isinstance(contexts, dict):
                                    if 'geo' in contexts:
                                        geo = contexts['geo']
                                        geo_info = {
                                            "country": geo.get('country_code'),
                                            "city": geo.get('city'),
                                            "region": geo.get('region')
                                        }
                                    
                                    browser_info = {}
                                    runtime_info = {}
                                    if 'browser' in contexts:
                                        browser = contexts['browser']
                                        browser_info = {
                                            "name": browser.get('name'),
                                            "version": browser.get('version')
                                        }
                                    
                                    if 'runtime' in contexts:
                                        runtime = contexts['runtime']
                                        runtime_info = {
                                            "name": runtime.get('name'),
                                            "version": runtime.get('version')
                                        }
                            
                            result["user_impact_summary"] = {
                                "user": user_context,
                                "geo_location": geo_info,
                                "browser": browser_info,
                                "runtime": runtime_info,
                                "trace_id": contexts.get('trace', {}).get('trace_id') if 'contexts' in latest_event else None
                            }
            except Exception as e:
                logger.warning(f"Failed to get latest event for issue {issue_id}: {e}")
                result["latest_event_summary"] = {"error": str(e)}

            try:
                events = self.get_issue_events(issue_id, limit=1)
                if isinstance(events, dict) and 'data' in events:
                    event_data = events['data']
                    if isinstance(event_data, list):
                        result["available_data"].append("events")
                        result["user_impact_summary"]["total_events"] = len(event_data)
            except Exception as e:
                logger.warning(f"Failed to get events for issue {issue_id}: {e}")
                result["events_summary"] = {"error": str(e)}

            try:
                notes = self.get_issue_notes(issue_id)
                if isinstance(notes, dict) and 'data' in notes:
                    notes_data = notes['data']
                    if isinstance(notes_data, list):
                        result["available_data"].append("notes")
                        result["notes_count"] = len(notes_data)
            except Exception as e:
                logger.warning(f"Failed to get notes for issue {issue_id}: {e}")
                result["notes_summary"] = {"error": str(e)}

            try:
                hashes = self.get_issue_hashes(issue_id)
                if isinstance(hashes, dict) and 'data' in hashes:
                    hashes_data = hashes['data']
                    if isinstance(hashes_data, list):
                        result["available_data"].append("hashes")
                        result["hashes_count"] = len(hashes_data)
            except Exception as e:
                logger.warning(f"Failed to get hashes for issue {issue_id}: {e}")
                result["hashes_summary"] = {"error": str(e)}

            return result

        except Exception as e:
            logger.error(f"Failed to get comprehensive issue details: {e}")
            return {"error": f"Failed to get comprehensive issue details: {str(e)}"}

    def get_issues_by_frequency(self, project_slug: str, limit: int = 100, since: Optional[float] = None, until: Optional[float] = None) -> Dict[str, Any]:
        """Get issues sorted by frequency (most occurring first)."""
        endpoint = f"/projects/{self.config.organization}/{project_slug}/issues/"
        params = {
            'limit': limit,
            'sort': 'freq',
            'statsPeriod': '24h'
        }
        
        if since:
            params['since'] = int(since)
        if until:
            params['until'] = int(until)
            
        return self._make_request('GET', endpoint, params=params)

    def get_issues_by_user_impact(self, project_slug: str, limit: int = 100, since: Optional[float] = None, until: Optional[float] = None) -> Dict[str, Any]:
        """Get issues sorted by user impact (most users affected first)."""
        endpoint = f"/projects/{self.config.organization}/{project_slug}/issues/"
        params = {
            'limit': limit,
            'sort': 'users',
            'statsPeriod': '24h'
        }
        
        if since:
            params['since'] = int(since)
        if until:
            params['until'] = int(until)
            
        return self._make_request('GET', endpoint, params=params)

    def get_release_health(self, project_slug: str, release: Optional[str] = None) -> Dict[str, Any]:
        """Get release health data for a project."""
        endpoint = f"/projects/{self.config.organization}/{project_slug}/releases/"
        params = {}
        if release:
            params['query'] = release
        return self._make_request('GET', endpoint, params=params)

    def get_project_performance(self, project_slug: str, query: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Get performance data for a project."""
        endpoint = f"/projects/{self.config.organization}/{project_slug}/events/"
        params = {'limit': limit, 'field': 'transaction', 'sort': '-timestamp'}
        if query:
            params['query'] = query
        return self._make_request('GET', endpoint, params=params)

    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects with caching."""
        current_time = datetime.now(timezone.utc)
        
        if (self._projects_cache["data"] is None or 
            self._projects_cache["timestamp"] is None or
            (current_time - self._projects_cache["timestamp"]).total_seconds() > self._projects_cache["cache_ttl"]):
            
            logger.info("Cache expired or empty, fetching projects from Sentry API")
            projects = self.get_organization_projects()
            self._projects_cache["data"] = projects
            self._projects_cache["timestamp"] = current_time
            logger.info(f"Fetched {len(projects)} projects")
        else:
            logger.info("Using cached projects data")
            
        return self._projects_cache["data"]

    async def find_matching_project(self, project_name: str = None) -> Dict[str, Any]:
        """Find the best matching project using AI if needed."""
        if not project_name:
            return {"error": "Project name is required"}

        # First try exact match
        projects = self.get_all_projects()
        exact_matches = [p for p in projects if p['slug'].lower() == project_name.lower()]
        if exact_matches:
            return {"project_slug": exact_matches[0]['slug'], "project_name": exact_matches[0]['name']}

        # Try partial match
        partial_matches = [p for p in projects if project_name.lower() in p['slug'].lower() or project_name.lower() in p['name'].lower()]
        if len(partial_matches) == 1:
            return {"project_slug": partial_matches[0]['slug'], "project_name": partial_matches[0]['name']}
        elif len(partial_matches) > 1:
            return await self._find_best_match_ai(project_name, partial_matches)
        else:
            return await self._find_best_match_ai(project_name, projects)

    async def _find_best_match_ai(self, target_name: str, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use AI to find the best matching project."""
        if not self.openai_api_key:
            return {"error": "OpenAI API key required for AI-powered name matching"}

        prompt = self._build_prompt(candidates, target_name)
        try:
            result = await self.call_llm(prompt)
            # Parse the result to extract the best match
            # This is a simplified implementation - you might want to make it more robust
            for project in candidates:
                if project['slug'].lower() in result.lower() or project['name'].lower() in result.lower():
                    return {"project_slug": project['slug'], "project_name": project['name']}
            
            if candidates:
                return {"project_slug": candidates[0]['slug'], "project_name": candidates[0]['name']}
            else:
                return {"error": f"No project found matching '{target_name}'"}
        except Exception as e:
            logger.error(f"AI matching failed: {e}")
            # Fallback to first candidate
            if candidates:
                return {"project_slug": candidates[0]['slug'], "project_name": candidates[0]['name']}
            else:
                return {"error": f"No project found matching '{target_name}'"}

    def _build_prompt(self, projects: List[Dict[str, Any]], target_name: str) -> str:
        """Build a prompt for AI-based project matching."""
        project_list = "\n".join([f"- {p['name']} (slug: {p['slug']})" for p in projects])
        
        prompt = f"""
        Given the target project name "{target_name}" and the following list of available projects:
        
        {project_list}
        
        Please identify the best matching project. Consider:
        1. Exact name matches
        2. Partial name matches
        3. Similar naming patterns
        4. Common abbreviations or variations
        
        Return only the slug of the best matching project. If no good match is found, return "no_match".
        """
        return prompt

    async def call_llm(self, prompt: str) -> str:
        """Call the LLM for AI-powered features."""
        try:
            response = await acompletion(
                model=self.model or "openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                api_key=self.openai_api_key
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
