"""CLI for Sentry MCP server."""
import os
import anyio
import argparse
import logging
from dotenv import load_dotenv
from sentry_mcp.server import SentryMCPServer
from sentry_mcp.client import SentryClientConfig

# Load environment variables from .env file if it exists
load_dotenv()

logger = logging.getLogger('sentry_mcp')

async def perform_async_initialization(server_obj: SentryMCPServer) -> None:
    """Initialize Sentry client asynchronously."""
    try:
        # Sentry client is initialized in the constructor
        # No need for explicit initialization
        pass
    except Exception as e:
        logger.error(f"Failed to initialize Sentry client: {e}")
        return 1

def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Sentry MCP Server")
    parser.add_argument("--sentry-api-token", type=str, help="Sentry API token")
    parser.add_argument("--sentry-org", type=str, help="Sentry organization slug")
    parser.add_argument("--sentry-host", default="https://sentry.io", type=str, help="Sentry host URL")
    parser.add_argument("--model", default="openai/gpt-4o-mini", type=str, help="OpenAI model to use")
    parser.add_argument("--openai-api-key", type=str, help="OpenAI API key")

    args = parser.parse_args()

    # Get values from environment variables if not provided as arguments
    sentry_api_token = args.sentry_api_token or os.getenv('SENTRY_API_TOKEN')
    sentry_org = args.sentry_org or os.getenv('SENTRY_ORG')
    sentry_host = args.sentry_host or os.getenv('SENTRY_HOST', 'https://sentry.io')
    openai_api_key = args.openai_api_key or os.getenv('OPENAI_API_KEY')

    if not sentry_api_token:
        logger.error("Missing required argument: sentry-api-token or SENTRY_API_TOKEN environment variable")
        return 1

    if not sentry_org:
        logger.error("Missing required argument: sentry-org or SENTRY_ORG environment variable")
        return 1

    if not openai_api_key:
        logger.error("Missing required argument: openai-api-key or OPENAI_API_KEY environment variable")
        return 1

    try:
        # Create Sentry client config
        sentry_config = SentryClientConfig(
            api_token=sentry_api_token,
            organization=sentry_org,
            host=sentry_host
        )

        # Create server instance
        server = SentryMCPServer(
            model=args.model,
            openai_api_key=openai_api_key,
            sentry_config=sentry_config
        )

        anyio.run(perform_async_initialization, server)
        server.run_mcp_blocking()
        return 0

    except Exception as e:
        logger.error(f"Error running server: {e}")
        return 1

if __name__ == "__main__":
    main()
