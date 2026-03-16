import logging

# Available Veo models on Vertex AI (as of March 2026)
VEO_MODELS = {
    "veo-3.1": "veo-3.1-generate-preview",       # Latest — best quality, image-to-video, audio
    "veo-3.0": "veo-3.0-generate-preview",        # Stable preview
    "veo-2.0": "veo-2.0-generate-001",            # GA stable — recommended for production
    "veo-2.0-exp": "veo-2.0-generate-exp",        # Experimental — supports style images
}

DEFAULT_MODEL = "veo-2.0-generate-001"

SUPPORTED_ASPECT_RATIOS = ["16:9", "9:16"]
SUPPORTED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_VIDEOS_PER_REQUEST = 4
MAX_DURATION_SECONDS = 30


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
