import base64
from typing import List

from config import GEMINI_API_KEY, GEMINI_MODEL
from models import ImageAttachment

SUPPORTED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024


def describe_images(images: List[ImageAttachment]) -> str:
    """Analyze attached images with Gemini before planning a reply."""
    if not images:
        return ""
    if not GEMINI_API_KEY:
        return "Image analysis is unavailable because GEMINI_API_KEY is not configured."

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)
        parts: list = [
            types.Part.from_text(
                "Analyze these user-provided images. Describe relevant visual details, "
                "extract visible text accurately, and identify errors or UI elements when "
                "present. Do not infer details that are not visible."
            )
        ]

        for image in images[:3]:
            if image.mime_type not in SUPPORTED_IMAGE_TYPES:
                return (
                    f"'{image.name}' is not a supported image type. "
                    "Use PNG, JPG, WebP, or GIF."
                )
            raw_data = base64.b64decode(image.data, validate=True)
            if len(raw_data) > MAX_IMAGE_BYTES:
                return f"'{image.name}' is larger than the 8 MB attachment limit."
            parts.append(types.Part.from_bytes(data=raw_data, mime_type=image.mime_type))

        if len(parts) == 1:
            return "No supported images were attached."

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=parts,
        )
        return response.text or "Gemini could not extract usable details from the image."
    except ImportError:
        return (
            "Image analysis is unavailable because the google-genai package is not installed."
        )
    except Exception as exc:
        return f"Gemini could not analyze the image: {str(exc)}"
