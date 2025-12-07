import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import schemas, services, models
from ..database.services import get_db
from .auth import get_current_user
from ..utils.paths import get_public_path


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=schemas.User)
def update_user_me(user_update: schemas.UserBase, current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Update fields
    user_data = user_update.model_dump(exclude_unset=True)
    for key, value in user_data.items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/complete-profile", response_model=schemas.User)
def complete_profile(
    profile_data: schemas.CompleteProfileRequest, 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Complete user profile with additional information.
    This is called after Google sign-in to collect missing user data.
    """
    # Update the profile fields
    profile_dict = profile_data.model_dump(exclude_unset=True)
    for key, value in profile_dict.items():
        if value is not None:
            setattr(current_user, key, value)
    
    # Mark profile as completed
    current_user.profile_completed = True
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/stats")
def read_user_stats(current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return services.get_user_stats(db, current_user.id)

@router.get("/activity", response_model=schemas.ResponseModel)
def read_user_activity(
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    total, rows = services.get_user_activity(db, current_user.id, page, page_size)
    names = [row.name for row in rows if getattr(row, "name", None)]
    stats_map = services.get_splice_stats_for_video_names(db, names)
    items: list[dict] = []

    for row in rows:
        public_path = get_public_path(getattr(row, "path", None))
        base_item = schemas.ActivityItem(
            id=row.id,
            name=row.name,
            path=public_path,
            label=row.label,
            origin=row.origin,
            duration=row.duration,
            validation=row.validation,
            owner_id=row.owner_id,
            labeler_id=row.labeler_id,
            validator_id=row.validator_id,
            activity_type=row.activity_type,
        )

        stats_payload = stats_map.get(row.name)
        if stats_payload:
            base_item = base_item.model_copy(
                update={"stats": schemas.UploadStats(**stats_payload)}
            )
        items.append(base_item.model_dump())

    total_pages = math.ceil(total / page_size) if total else 0
    return schemas.ResponseModel(
        status="success",
        data={
            "items": items,
            "meta": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            },
        },
        message="Activity history retrieved",
    )
