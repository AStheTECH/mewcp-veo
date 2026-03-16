import json
import logging

from fastmcp import FastMCP
from pydantic import Field

from .schemas import VeoAuth
from .config import VEO_MODELS, DEFAULT_MODEL
from .service import start_video_generation, poll_operation

logger = logging.getLogger("veo-mcp-server")


def register_tools(mcp: FastMCP) -> None:

    # ═══════════════════════════════════════════════════════════
    # 🎬 VIDEO GENERATION TOOLS
    # ═══════════════════════════════════════════════════════════

    @mcp.tool(
        name="generate_video_from_text",
        description=(
            "Generate a video from a text prompt using Vertex AI Veo. "
            "This starts a long-running job and polls until completion. "
            "Returns video bytes or a Cloud Storage URI."
        ),
    )
    def generate_video_from_text(
        auth: VeoAuth = Field(..., description="Vertex AI credentials"),
        prompt: str = Field(..., description="Text prompt describing the video to generate"),
        model: str = Field(default="veo-2.0", description="Model to use: veo-3.1 | veo-3.0 | veo-2.0 | veo-2.0-exp"),
        aspect_ratio: str = Field(default="16:9", description="Aspect ratio: '16:9' or '9:16'"),
        duration_seconds: int = Field(default=5, description="Video duration in seconds (1–30)"),
        count: int = Field(default=1, description="Number of videos to generate (1–4)"),
        output_gcs_uri: str = Field(default="", description="Optional GCS bucket URI to store output, e.g. 'gs://my-bucket/output/'"),
    ) -> str:
        try:
            model_id = VEO_MODELS.get(model, DEFAULT_MODEL)
            payload = {
                "instances": [{"prompt": prompt}],
                "parameters": {
                    "aspectRatio": aspect_ratio,
                    "videoLength": str(duration_seconds),
                    "sampleCount": count,
                },
            }
            if output_gcs_uri:
                payload["parameters"]["storageUri"] = output_gcs_uri

            operation = start_video_generation(auth, payload, model_id)
            operation_name = operation.get("name", "")

            if not operation_name:
                return json.dumps({"error": "No operation name returned", "raw": operation})

            result = poll_operation(auth, operation_name)
            return json.dumps({
                "operation_name": operation_name,
                "result": result,
            })
        except Exception as e:
            logger.error(f"Failed to generate video from text: {e}")
            return json.dumps({"error": str(e)})

    @mcp.tool(
        name="generate_video_from_image",
        description=(
            "Generate a video from an image + text prompt using Vertex AI Veo. "
            "The image becomes the first frame of the video. "
            "Supports base64-encoded images or GCS URIs."
        ),
    )
    def generate_video_from_image(
        auth: VeoAuth = Field(..., description="Vertex AI credentials"),
        prompt: str = Field(..., description="Text prompt to guide the video generation"),
        image_gcs_uri: str = Field(default="", description="GCS URI of input image, e.g. 'gs://my-bucket/image.jpg'"),
        image_base64: str = Field(default="", description="Base64-encoded image bytes (use this OR image_gcs_uri)"),
        image_mime_type: str = Field(default="image/jpeg", description="MIME type: image/jpeg | image/png | image/webp"),
        model: str = Field(default="veo-2.0", description="Model to use: veo-3.1 | veo-3.0 | veo-2.0"),
        aspect_ratio: str = Field(default="16:9", description="Aspect ratio: '16:9' or '9:16'"),
        duration_seconds: int = Field(default=5, description="Video duration in seconds (1–30)"),
        count: int = Field(default=1, description="Number of videos to generate (1–4)"),
        output_gcs_uri: str = Field(default="", description="Optional GCS bucket URI to store output"),
    ) -> str:
        try:
            model_id = VEO_MODELS.get(model, DEFAULT_MODEL)

            # Build image reference
            if image_gcs_uri:
                image_ref = {"gcsUri": image_gcs_uri, "mimeType": image_mime_type}
            elif image_base64:
                image_ref = {"bytesBase64Encoded": image_base64, "mimeType": image_mime_type}
            else:
                return json.dumps({"error": "Provide either image_gcs_uri or image_base64"})

            payload = {
                "instances": [{
                    "prompt": prompt,
                    "image": image_ref,
                }],
                "parameters": {
                    "aspectRatio": aspect_ratio,
                    "videoLength": str(duration_seconds),
                    "sampleCount": count,
                },
            }
            if output_gcs_uri:
                payload["parameters"]["storageUri"] = output_gcs_uri

            operation = start_video_generation(auth, payload, model_id)
            operation_name = operation.get("name", "")

            if not operation_name:
                return json.dumps({"error": "No operation name returned", "raw": operation})

            result = poll_operation(auth, operation_name)
            return json.dumps({
                "operation_name": operation_name,
                "result": result,
            })
        except Exception as e:
            logger.error(f"Failed to generate video from image: {e}")
            return json.dumps({"error": str(e)})

    @mcp.tool(
        name="generate_video_from_first_and_last_frame",
        description=(
            "Generate a video by specifying both the first AND last frame images. "
            "Veo will interpolate the motion between them. "
            "Requires veo-2.0 model."
        ),
    )
    def generate_video_from_first_and_last_frame(
        auth: VeoAuth = Field(..., description="Vertex AI credentials"),
        prompt: str = Field(..., description="Text prompt to guide the video generation"),
        first_frame_gcs_uri: str = Field(..., description="GCS URI of the first frame image"),
        last_frame_gcs_uri: str = Field(..., description="GCS URI of the last frame image"),
        image_mime_type: str = Field(default="image/jpeg", description="MIME type: image/jpeg | image/png | image/webp"),
        aspect_ratio: str = Field(default="16:9", description="Aspect ratio: '16:9' or '9:16'"),
        duration_seconds: int = Field(default=5, description="Video duration in seconds (1–30)"),
        count: int = Field(default=1, description="Number of videos to generate (1–4)"),
        output_gcs_uri: str = Field(default="", description="Optional GCS bucket URI to store output"),
    ) -> str:
        try:
            model_id = VEO_MODELS["veo-2.0"]  # only veo-2.0 supports first+last frame
            payload = {
                "instances": [{
                    "prompt": prompt,
                    "firstFrame": {"gcsUri": first_frame_gcs_uri, "mimeType": image_mime_type},
                    "lastFrame":  {"gcsUri": last_frame_gcs_uri,  "mimeType": image_mime_type},
                }],
                "parameters": {
                    "aspectRatio": aspect_ratio,
                    "videoLength": str(duration_seconds),
                    "sampleCount": count,
                },
            }
            if output_gcs_uri:
                payload["parameters"]["storageUri"] = output_gcs_uri

            operation = start_video_generation(auth, payload, model_id)
            operation_name = operation.get("name", "")

            if not operation_name:
                return json.dumps({"error": "No operation name returned", "raw": operation})

            result = poll_operation(auth, operation_name)
            return json.dumps({
                "operation_name": operation_name,
                "result": result,
            })
        except Exception as e:
            logger.error(f"Failed to generate video from first/last frames: {e}")
            return json.dumps({"error": str(e)})

    @mcp.tool(
        name="extend_video",
        description=(
            "Extend an existing Veo-generated video by generating new footage "
            "that continues seamlessly from the last second of the input video. "
            "Great for creating longer scenes."
        ),
    )
    def extend_video(
        auth: VeoAuth = Field(..., description="Vertex AI credentials"),
        prompt: str = Field(..., description="Text prompt describing how to extend the video"),
        video_gcs_uri: str = Field(..., description="GCS URI of the video to extend, e.g. 'gs://my-bucket/input/video.mp4'"),
        model: str = Field(default="veo-2.0", description="Model to use: veo-3.1 | veo-3.0 | veo-2.0"),
        aspect_ratio: str = Field(default="16:9", description="Aspect ratio: '16:9' or '9:16'"),
        duration_seconds: int = Field(default=5, description="Duration of the new extension segment (1–30)"),
        count: int = Field(default=1, description="Number of extended videos to generate (1–4)"),
        output_gcs_uri: str = Field(default="", description="Optional GCS bucket URI to store output"),
    ) -> str:
        try:
            model_id = VEO_MODELS.get(model, DEFAULT_MODEL)
            payload = {
                "instances": [{
                    "prompt": prompt,
                    "video": {"gcsUri": video_gcs_uri},
                }],
                "parameters": {
                    "aspectRatio": aspect_ratio,
                    "videoLength": str(duration_seconds),
                    "sampleCount": count,
                },
            }
            if output_gcs_uri:
                payload["parameters"]["storageUri"] = output_gcs_uri

            operation = start_video_generation(auth, payload, model_id)
            operation_name = operation.get("name", "")

            if not operation_name:
                return json.dumps({"error": "No operation name returned", "raw": operation})

            result = poll_operation(auth, operation_name)
            return json.dumps({
                "operation_name": operation_name,
                "result": result,
            })
        except Exception as e:
            logger.error(f"Failed to extend video: {e}")
            return json.dumps({"error": str(e)})

    @mcp.tool(
        name="generate_video_with_style_reference",
        description=(
            "Generate a video using a style reference image to control the visual aesthetic. "
            "Only supported by veo-2.0-exp model."
        ),
    )
    def generate_video_with_style_reference(
        auth: VeoAuth = Field(..., description="Vertex AI credentials"),
        prompt: str = Field(..., description="Text prompt describing the video content"),
        style_image_gcs_uri: str = Field(..., description="GCS URI of style reference image"),
        style_image_mime_type: str = Field(default="image/jpeg", description="MIME type of style image"),
        aspect_ratio: str = Field(default="16:9", description="Aspect ratio: '16:9' or '9:16'"),
        duration_seconds: int = Field(default=5, description="Video duration in seconds"),
        count: int = Field(default=1, description="Number of videos to generate (1–4)"),
        output_gcs_uri: str = Field(default="", description="Optional GCS bucket URI to store output"),
    ) -> str:
        try:
            model_id = VEO_MODELS["veo-2.0-exp"]  # only exp supports style images
            payload = {
                "instances": [{
                    "prompt": prompt,
                    "referenceImages": [{
                        "referenceType": "REFERENCE_TYPE_STYLE",
                        "referenceImage": {
                            "gcsUri": style_image_gcs_uri,
                            "mimeType": style_image_mime_type,
                        },
                    }],
                }],
                "parameters": {
                    "aspectRatio": aspect_ratio,
                    "videoLength": str(duration_seconds),
                    "sampleCount": count,
                },
            }
            if output_gcs_uri:
                payload["parameters"]["storageUri"] = output_gcs_uri

            operation = start_video_generation(auth, payload, model_id)
            operation_name = operation.get("name", "")

            if not operation_name:
                return json.dumps({"error": "No operation name returned", "raw": operation})

            result = poll_operation(auth, operation_name)
            return json.dumps({
                "operation_name": operation_name,
                "result": result,
            })
        except Exception as e:
            logger.error(f"Failed to generate video with style reference: {e}")
            return json.dumps({"error": str(e)})

    # ═══════════════════════════════════════════════════════════
    # 🔄 OPERATION TOOLS
    # ═══════════════════════════════════════════════════════════

    @mcp.tool(
        name="get_operation_status",
        description=(
            "Check the status of a long-running Veo video generation operation. "
            "Use this if a generation timed out or you want to check progress manually."
        ),
    )
    def get_operation_status(
        auth: VeoAuth = Field(..., description="Vertex AI credentials"),
        operation_name: str = Field(..., description="Operation name returned from a generate_video_* tool"),
    ) -> str:
        try:
            result = poll_operation(auth, operation_name, max_wait=10)
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Failed to get operation status: {e}")
            return json.dumps({"error": str(e)})

    @mcp.tool(
        name="list_available_models",
        description="List all available Veo models and their capabilities.",
    )
    def list_available_models(
        auth: VeoAuth = Field(..., description="Vertex AI credentials"),
    ) -> str:
        models = {
            "veo-3.1": {
                "model_id": VEO_MODELS["veo-3.1"],
                "status": "Preview",
                "features": ["text-to-video", "image-to-video", "video-extend", "native-audio", "subject-reference"],
                "notes": "Latest model. Does NOT support style reference images.",
            },
            "veo-3.0": {
                "model_id": VEO_MODELS["veo-3.0"],
                "status": "Preview",
                "features": ["text-to-video", "image-to-video", "video-extend"],
                "notes": "Stable preview.",
            },
            "veo-2.0": {
                "model_id": VEO_MODELS["veo-2.0"],
                "status": "GA (recommended for production)",
                "features": ["text-to-video", "image-to-video", "first-last-frame", "video-extend"],
                "notes": "Most stable. Use for production workloads.",
            },
            "veo-2.0-exp": {
                "model_id": VEO_MODELS["veo-2.0-exp"],
                "status": "Experimental",
                "features": ["text-to-video", "image-to-video", "style-reference"],
                "notes": "Use this when you need style reference images.",
            },
        }
        return json.dumps(models, indent=2)
