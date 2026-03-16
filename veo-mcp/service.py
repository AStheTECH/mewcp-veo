import logging
import time
import requests
from typing import Any

from .schemas import VeoAuth
from .config import DEFAULT_MODEL

logger = logging.getLogger("veo-mcp-server")

VERTEX_AI_BASE = "https://{location}-aiplatform.googleapis.com/v1"


def get_headers(auth: VeoAuth) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {auth.get('access_token', '')}",
        "Content-Type": "application/json",
    }


def get_endpoint(auth: VeoAuth, model_id: str) -> str:
    location = auth.get("location") or "us-central1"
    project_id = auth.get("project_id", "")
    base = VERTEX_AI_BASE.format(location=location)
    return (
        f"{base}/projects/{project_id}/locations/{location}"
        f"/publishers/google/models/{model_id}:predictLongRunning"
    )


def get_operation_endpoint(auth: VeoAuth, operation_name: str) -> str:
    location = auth.get("location") or "us-central1"
    base = VERTEX_AI_BASE.format(location=location)
    # operation_name is like: projects/.../locations/.../operations/xxx
    return f"{base}/{operation_name}"


def start_video_generation(auth: VeoAuth, payload: dict[str, Any], model_id: str) -> dict:
    """Submit a video generation job and return the operation details."""
    url = get_endpoint(auth, model_id)
    headers = get_headers(auth)
    logger.info(f"Submitting video generation job to model: {model_id}")
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def poll_operation(auth: VeoAuth, operation_name: str, max_wait: int = 300) -> dict:
    """Poll a long-running operation until it completes or times out."""
    location = auth.get("location") or "us-central1"
    base = VERTEX_AI_BASE.format(location=location)
    url = f"{base}/{operation_name}"
    headers = get_headers(auth)

    logger.info(f"Polling operation: {operation_name}")
    elapsed = 0
    interval = 10  # poll every 10 seconds

    while elapsed < max_wait:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("done"):
            logger.info("Operation completed!")
            return data

        logger.info(f"Still processing... ({elapsed}s elapsed)")
        time.sleep(interval)
        elapsed += interval

    return {"error": f"Operation timed out after {max_wait} seconds. Use get_operation_status with the operation name to check later."}
