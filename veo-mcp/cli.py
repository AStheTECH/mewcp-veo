import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Vertex AI Veo MCP Server")
    parser.add_argument(
        "-t", "--transport",
        help="Transport method: 'stdio', 'sse', or 'streamable-http'",
        default=None,
    )
    parser.add_argument("--host", help="Host to bind to", default=None)
    parser.add_argument("--port", type=int, help="Port to bind to", default=None)
    return parser.parse_args()
