from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import schemas, services, models
from ..database.services import get_db
from .auth import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["users"]
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

@router.get("/activity", response_model=list[schemas.HighQualityLabeledSplice])
def read_user_activity(current_user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return services.get_user_activity(db, current_user.id)
