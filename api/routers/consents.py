from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import schemas, services
from ..database.services import get_db

router = APIRouter(
    prefix="/consents",
    tags=["Policies & Consent"],
)


@router.get("/latest", response_model=schemas.ResponseModel[schemas.PolicyConsent], summary="Fetch the latest published consent version")
def get_latest_consent(db: Session = Depends(get_db)) -> schemas.ResponseModel[schemas.PolicyConsent]:
    consent = services.get_latest_policy_consent(db)
    if consent is None:
        return schemas.ResponseModel(status="success", data=None, message="No consent versions configured.")

    return schemas.ResponseModel(
        status="success",
        data=consent,
        message="Latest consent version",
    )
