from __future__ import annotations

import os

from fastapi import APIRouter

from ..database import schemas
from ..services.mail import send_support_message


router = APIRouter(
    prefix="/support",
    tags=["Support"],
)


@router.post("/message", response_model=schemas.ResponseModel)
def submit_support_message(payload: schemas.SupportMessageRequest):
    """Accept a support/report message and forward it to the operator's support inbox."""

    support_email = os.getenv("SUPPORT_EMAIL", "support@uneduashqiperine.com")
    ok = send_support_message(
        support_email=support_email,
        from_email=str(payload.email),
        from_name=f"{payload.name} {payload.surname}".strip(),
        message=payload.message,
    )

    if not ok:
        return schemas.ResponseModel(
            status="error",
            data=None,
            message="Unable to send message right now. Please try again later.",
        )

    return schemas.ResponseModel(status="success", data=None, message="Message sent")
