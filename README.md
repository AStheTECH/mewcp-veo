# Vertex AI Veo MCP Server

A stateless Python MCP server for **Google's Vertex AI Veo API** — generate videos from text, images, first/last frames, and extend existing videos. Built with `fastmcp`, following the same patterns as the Google Meet, Google Business, and Zomato MCP servers.

---

## What it does

| Category | Tools |
|---|---|
| 🎬 Video Generation | `generate_video_from_text`, `generate_video_from_image`, `generate_video_from_first_and_last_frame`, `extend_video`, `generate_video_with_style_reference` |
| 🔄 Operations | `get_operation_status`, `list_available_models` |

**Total: 7 tools**

---

## Available Models

| Key | Model ID | Status | Best for |
|---|---|---|---|
| `veo-3.1` | veo-3.1-generate-preview | Preview | Latest quality, native audio, subject reference |
| `veo-3.0` | veo-3.0-generate-preview | Preview | Stable preview |
| `veo-2.0` | veo-2.0-generate-001 | **GA ✅** | Production workloads |
| `veo-2.0-exp` | veo-2.0-generate-exp | Experimental | Style reference images |

---

## Auth — credentials format

Every tool accepts a `VeoAuth` object:

```json
{
  "project_id": "your-google-cloud-project-id",
  "location": "us-central1",
  "access_token": "ya29.your_oauth2_access_token"
}
```

### Getting an access token

**Option 1 — gcloud CLI (easiest for testing):**
```bash
gcloud auth login
gcloud auth print-access-token
```

**Option 2 — Service Account (recommended for production):**
```bash
gcloud iam service-accounts create veo-mcp-sa
gcloud projects add-iam-policy-binding YOUR_PROJECT \
  --member="serviceAccount:veo-mcp-sa@YOUR_PROJECT.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
gcloud iam service-accounts keys create service_account.json \
  --iam-account=veo-mcp-sa@YOUR_PROJECT.iam.gserviceaccount.com
```

Then get a token from the service account:
```python
from google.oauth2 import service_account
import google.auth.transport.requests

creds = service_account.Credentials.from_service_account_file(
    'service_account.json',
    scopes=['https://www.googleapis.com/auth/cloud-platform']
)
creds.refresh(google.auth.transport.requests.Request())
print(creds.token)
```

---

## Setup

### 1. Enable the Vertex AI API

In [Google Cloud Console](https://console.cloud.google.com):
- Go to **APIs & Services → Library**
- Search **"Vertex AI API"** → **Enable**

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the server

```bash
python veo_mcp_server.py --transport stdio
```

---

## Connect to Claude Desktop

```json
{
  "mcpServers": {
    "veo": {
      "command": "python",
      "args": ["/absolute/path/to/veo_mcp_server.py", "--transport", "stdio"]
    }
  }
}
```

---

## Tool Examples

### Text to Video
```json
{
  "auth": { "project_id": "my-project", "location": "us-central1", "access_token": "ya29.xxx" },
  "prompt": "A golden retriever running on a beach at sunset",
  "model": "veo-2.0",
  "aspect_ratio": "16:9",
  "duration_seconds": 5,
  "count": 1,
  "output_gcs_uri": "gs://my-bucket/videos/"
}
```

### Image to Video
```json
{
  "auth": { ... },
  "prompt": "The flowers gently sway in the breeze",
  "image_gcs_uri": "gs://my-bucket/flowers.jpg",
  "image_mime_type": "image/jpeg",
  "model": "veo-3.1",
  "duration_seconds": 5
}
```

### First + Last Frame
```json
{
  "auth": { ... },
  "prompt": "A smooth transition from sunrise to sunset",
  "first_frame_gcs_uri": "gs://my-bucket/sunrise.jpg",
  "last_frame_gcs_uri": "gs://my-bucket/sunset.jpg",
  "duration_seconds": 8
}
```

### Extend Video
```json
{
  "auth": { ... },
  "prompt": "Continue the scene, camera pans right",
  "video_gcs_uri": "gs://my-bucket/input/clip.mp4",
  "duration_seconds": 5,
  "model": "veo-3.1"
}
```

---

## ⚠️ Important Notes

- Video generation is a **long-running operation** (typically 30–120 seconds) — the tools automatically poll until completion
- If polling times out, use `get_operation_status` with the returned `operation_name` to check later
- For `output_gcs_uri` — you must have a GCS bucket created in advance. If not provided, video bytes are returned inline in the response
- Pricing: approximately **$0.03/second** of generated video on Vertex AI

---

## Project Structure

```
veo-mcp/
├── veo_mcp_server.py     # Entry point
├── veo_mcp/
│   ├── tools.py          # All 7 tool definitions
│   ├── service.py        # Vertex AI API client + operation polling
│   ├── schemas.py        # VeoAuth TypedDict
│   ├── config.py         # Model registry + logging
│   ├── cli.py            # CLI args parser
│   └── __init__.py
├── requirements.txt
├── Dockerfile
├── railway.json
└── .gitignore
```
