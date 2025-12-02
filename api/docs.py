"""Custom API documentation helpers for the DibraSpeaks platform."""
from __future__ import annotations

from textwrap import dedent
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse

API_TITLE = "DibraSpeaks API"
API_VERSION = "1.1.0"
API_DESCRIPTION = dedent(
    """
    Minimal, contract-first interface for DibraSpeaks ingestion, labeling, validation, and reporting. All
    responses follow the shared success/error envelopes documented in `STANDARDS.md`.
    """
)
CONTACT_INFO = {
    "name": "DibraSpeaks Platform Team",
    "url": "https://uneduashqiperine.com/api",
}
LICENSE_INFO = {
    "name": "Apache License 2.0",
    "url": "https://www.apache.org/licenses/LICENSE-2.0",
}
TERMS_OF_SERVICE = "https://uneduashqiperine.com/terms"
LOGO_URL = "https://raw.githubusercontent.com/florijanqosja/Albanian-ASR/master/web/public/logo.png"

TAGS_METADATA = [
    {
        "name": "Authentication",
        "description": "Registration, login, refresh tokens, and third-party (Google) sign-in flows.",
    },
    {
        "name": "Users",
        "description": "Profile completion, preference updates, and contributor-facing statistics.",
    },
    {
        "name": "Video Intake",
        "description": "Endpoints that ingest long-form media, convert to MP3, splice, and seed queues.",
    },
    {
        "name": "Labeling Queue",
        "description": "Fetch and reserve splice work items for labeling or validation with cache-safe URLs.",
    },
    {
        "name": "Labeling Actions",
        "description": "Submit transcripts, optional trims, and route clips through the labeling pipeline.",
    },
    {
        "name": "Validation Actions",
        "description": "Finalize labeled clips, promote them into the high-quality corpus, and ensure dual review.",
    },
    {
        "name": "Dataset Insights",
        "description": "Operational metrics covering throughput, durations, and splice counts per stage.",
    },
    {
        "name": "Operational Utilities",
        "description": "Low-level helpers for sample clips, IDs, and maintenance workflows.",
    },
]

SERVERS_METADATA = [
    {"url": "https://uneduashqiperine.com/api", "description": "Production"},
    {"url": "http://localhost:8000", "description": "Local development"},
]

EXTERNAL_DOCS = {
    "description": "Contribute or review implementation details on GitHub",
    "url": "https://github.com/florijanqosja/Albanian-ASR",
}

SWAGGER_UI_PARAMETERS = {
    "deepLinking": True,
    "displayRequestDuration": True,
    "defaultModelsExpandDepth": -1,
    "defaultModelExpandDepth": 1,
    "docExpansion": "none",
    "operationsSorter": "alpha",
    "tagsSorter": "alpha",
    "persistAuthorization": True,
}

SWAGGER_HERO = ""

REDOC_HERO = ""

CUSTOM_STYLE = dedent(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Khula:wght@400;600;700&display=swap');
        :root {
            --ds-primary: #A64D4A;
            --ds-accent: #FFE4E6;
            --ds-border: #FECACA;
            --ds-surface: #FFFFFF;
            --ds-text: #404040;
        }
        body {
            font-family: 'Khula', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f9f6f6;
            color: var(--ds-text);
            margin: 0;
        }
        .swagger-ui .topbar {
            background-color: var(--ds-primary);
            padding: 16px 32px;
            box-shadow: none;
            border-bottom: 1px solid rgba(0,0,0,0.05);
        }
        .swagger-ui .topbar .download-url-wrapper {
            display: none;
        }
        .swagger-ui .topbar a.link span {
            color: #fff !important;
            font-weight: 600;
            letter-spacing: 0.04em;
        }
        .swagger-ui .info,
        .swagger-ui .scheme-container {
            border-radius: 12px;
            border: 1px solid rgba(0,0,0,0.05);
            padding: 24px;
            background: #fff;
        }
        .swagger-ui .info hgroup.main h2 {
            font-size: 40px;
            font-weight: 700;
        }
        .swagger-ui .info p {
            font-size: 17px;
            line-height: 1.55;
        }
        .swagger-ui .opblock-summary {
            border-left: 4px solid transparent;
        }
        .swagger-ui .opblock-summary-method {
            border-radius: 8px;
        }
        .swagger-ui .opblock-tag {
            font-size: 20px;
            font-weight: 600;
            color: var(--ds-primary);
        }
        .swagger-ui .btn.authorize span {
            color: var(--ds-primary);
            font-weight: 600;
        }
        .swagger-ui .btn.authorize {
            border-radius: 12px;
            border: 1px solid var(--ds-border);
            background: var(--ds-accent);
            color: var(--ds-primary);
            box-shadow: none;
        }
    </style>
    """
)

REDOC_STYLE = dedent(
    """
    <style>
        body {
            font-family: 'Khula', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f9f6f6;
        }
        .redoc-wrap {
            margin-top: -32px;
        }
    </style>
    """
)


def _inject_branding(original: HTMLResponse, hero_markup: str, extra_head: str) -> HTMLResponse:
    """Injects custom hero sections and CSS into a generated HTMLResponse."""
    content = original.body.decode("utf-8")
    if extra_head:
        content = content.replace("</head>", f"{extra_head}</head>", 1)
    if hero_markup:
        if "<div id=\"swagger-ui\"></div>" in content:
            content = content.replace(
                "<div id=\"swagger-ui\"></div>",
                f"{hero_markup}<div id=\"swagger-ui\"></div>",
                1,
            )
        else:
            content = content.replace("<body>", f"<body>{hero_markup}", 1)
        content = content.replace("<body>", "<body class=\"ds-docs\">", 1)
    headers = {
        key: value
        for key, value in dict(original.headers).items()
        if key.lower() != "content-length"
    }
    return HTMLResponse(
        content=content,
        status_code=original.status_code,
        headers=headers,
        media_type=original.media_type,
    )


def configure_documentation(app: FastAPI) -> None:
    """Attach OpenAPI metadata and register branded documentation routes."""

    root_path = (app.root_path or "").rstrip("/")

    def _with_root(path: str) -> str:
        """Prefix absolute paths with the app's root_path when defined."""
        if not path.startswith("/"):
            return path
        return f"{root_path}{path}" if root_path else path

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=API_TITLE,
            version=API_VERSION,
            description=API_DESCRIPTION,
            routes=app.routes,
            tags=TAGS_METADATA,
        )
        openapi_schema["info"]["contact"] = CONTACT_INFO
        openapi_schema["info"]["license"] = LICENSE_INFO
        openapi_schema["info"]["termsOfService"] = TERMS_OF_SERVICE
        openapi_schema["info"]["x-logo"] = {
            "url": LOGO_URL,
            "altText": "DibraSpeaks logo",
        }
        openapi_schema["servers"] = SERVERS_METADATA
        openapi_schema["externalDocs"] = EXTERNAL_DOCS
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[assignment]

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui() -> HTMLResponse:  # pragma: no cover - UI route
        openapi_url = _with_root(app.openapi_url)
        html = get_swagger_ui_html(
            openapi_url=openapi_url,
            title=f"{API_TITLE} Explorer",
            oauth2_redirect_url=_with_root("/docs/oauth2-redirect"),
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
            swagger_ui_parameters=SWAGGER_UI_PARAMETERS,
        )
        return _inject_branding(html, SWAGGER_HERO, CUSTOM_STYLE)

    @app.get("/docs/oauth2-redirect", include_in_schema=False)
    async def swagger_redirect() -> HTMLResponse:  # pragma: no cover - UI route
        return get_swagger_ui_oauth2_redirect_html()

    @app.get("/redoc", include_in_schema=False)
    async def redoc_ui() -> HTMLResponse:  # pragma: no cover - UI route
        openapi_url = _with_root(app.openapi_url)
        html = get_redoc_html(
            openapi_url=openapi_url,
            title=f"{API_TITLE} Reference",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
            with_google_fonts=False,
        )
        return _inject_branding(html, REDOC_HERO, REDOC_STYLE)
