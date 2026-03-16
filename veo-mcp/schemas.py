from typing_extensions import TypedDict


class VeoAuth(TypedDict, total=False):
    project_id: str       # Google Cloud project ID
    location: str         # Region, e.g. "us-central1" or "global"
    access_token: str     # OAuth2 access token (from gcloud auth print-access-token)
