"""Shared filesystem path utilities for mapping static assets to public URLs."""
from __future__ import annotations

import os
from typing import Optional

IS_PRODUCTION = os.getenv("ENVIRONMENT") == "production"
BASE_DIR = "/code" if os.path.exists("/code") else "."

UPLOAD_DIR_MP4 = os.path.join(BASE_DIR, "mp4")
UPLOAD_DIR_MP3 = os.path.join(BASE_DIR, "mp3")
SPLICES_DIR = os.path.join(BASE_DIR, "splices")

UPLOAD_DIR_MP4_ABS = os.path.abspath(UPLOAD_DIR_MP4)
UPLOAD_DIR_MP3_ABS = os.path.abspath(UPLOAD_DIR_MP3)
SPLICES_DIR_ABS = os.path.abspath(SPLICES_DIR)


def get_public_path(file_path: Optional[str], include_version: bool = True) -> Optional[str]:
    """Convert a filesystem path into a public static mount path.

    Returns paths rooted at `/splices`, `/mp3`, or `/mp4` when the input resides under
    the corresponding storage directories. Unknown paths fall back to their absolute
    locations so callers can still inspect them.
    """

    if not file_path:
        return file_path

    normalized_path = os.path.abspath(file_path)

    def _relativize(base_dir: str, mount_point: str) -> Optional[str]:
        if normalized_path.startswith(base_dir):
            relative_path = normalized_path[len(base_dir) :]
            if not relative_path.startswith("/"):
                relative_path = "/" + relative_path
            return f"{mount_point}{relative_path}"
        return None

    public_path = None
    for directory, mount_point in (
        (SPLICES_DIR_ABS, "/splices"),
        (UPLOAD_DIR_MP3_ABS, "/mp3"),
        (UPLOAD_DIR_MP4_ABS, "/mp4"),
    ):
        public_path = _relativize(directory, mount_point)
        if public_path:
            break

    if not public_path:
        return normalized_path

    if include_version:
        try:
            version = int(os.path.getmtime(normalized_path))
            separator = "&" if "?" in public_path else "?"
            return f"{public_path}{separator}v={version}"
        except OSError:
            # File might not exist anymore; return the path without cache busting.
            return public_path

    return public_path
