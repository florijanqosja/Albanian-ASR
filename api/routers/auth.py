from datetime import datetime, timedelta
from typing import Optional
import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from pydantic import BaseModel

from ..database import schemas, services, models
from ..database.services import get_db
from ..services.mail import (
    generate_verification_code,
    send_verification_email,
    send_welcome_email,
    send_password_reset_email
)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

# Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
VERIFICATION_CODE_EXPIRE_MINUTES = 15
RESET_CODE_EXPIRE_MINUTES = 15

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: str = payload.get("id")
        if email is None or user_id is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email, user_id=user_id)
    except JWTError:
        raise credentials_exception
    user = services.get_user(db, user_id=token_data.user_id)
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=schemas.RegisterResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user and send a verification email.
    The user will need to verify their email before they can log in.
    """
    db_user = services.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    
    # Generate verification code
    verification_code = generate_verification_code()
    verification_code_expires = datetime.utcnow() + timedelta(minutes=VERIFICATION_CODE_EXPIRE_MINUTES)
    
    # Create the user (not verified yet)
    new_user = services.create_user(
        db=db, 
        user=user, 
        hashed_password=hashed_password,
        verification_code=verification_code,
        verification_code_expires=verification_code_expires
    )
    
    # Send verification email (don't fail registration if email fails)
    try:
        send_verification_email(user.email, verification_code, user.name)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to send verification email: {e}")
    
    return schemas.RegisterResponse(
        message="Registration successful. Please check your email for the verification code.",
        email=user.email
    )


@router.post("/verify-email", response_model=schemas.Token)
def verify_email(request: schemas.VerifyEmailRequest, db: Session = Depends(get_db)):
    """
    Verify a user's email using the code sent to their email.
    Returns an access token on successful verification.
    """
    user = services.get_user_by_email(db, email=request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    if not user.verification_code or user.verification_code != request.code:
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    if user.verification_code_expires and datetime.utcnow() > user.verification_code_expires:
        raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new one.")
    
    # Mark user as verified
    user.is_verified = True
    user.verification_code = None
    user.verification_code_expires = None
    db.commit()
    db.refresh(user)
    
    # Send welcome email (don't fail verification if email fails)
    try:
        send_welcome_email(user.email, user.name)
    except Exception as e:
        # Log the error but don't fail the verification
        import logging
        logging.getLogger(__name__).error(f"Failed to send welcome email: {e}")
    
    # Generate access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "id": user.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/resend-verification")
def resend_verification(request: schemas.ResendVerificationRequest, db: Session = Depends(get_db)):
    """
    Resend the verification code to a user's email.
    """
    user = services.get_user_by_email(db, email=request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Generate new verification code
    verification_code = generate_verification_code()
    user.verification_code = verification_code
    user.verification_code_expires = datetime.utcnow() + timedelta(minutes=VERIFICATION_CODE_EXPIRE_MINUTES)
    db.commit()
    
    # Send verification email (don't fail if email fails)
    try:
        send_verification_email(user.email, verification_code, user.name)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to send verification email: {e}")
    
    return {"message": "Verification code sent. Please check your email."}


@router.post("/forgot-password")
def forgot_password(request: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Send a password reset code to the user's email.
    """
    user = services.get_user_by_email(db, email=request.email)
    if not user:
        # Don't reveal if the email exists or not for security
        return {"message": "If an account with that email exists, a password reset code has been sent."}
    
    if user.provider != "local":
        raise HTTPException(
            status_code=400, 
            detail=f"This account uses {user.provider} login. Please use that method to sign in."
        )
    
    # Generate reset code
    reset_code = generate_verification_code()
    user.reset_code = reset_code
    user.reset_code_expires = datetime.utcnow() + timedelta(minutes=RESET_CODE_EXPIRE_MINUTES)
    db.commit()
    
    # Send password reset email (don't fail if email fails)
    try:
        send_password_reset_email(user.email, reset_code, user.name)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to send password reset email: {e}")
    
    return {"message": "If an account with that email exists, a password reset code has been sent."}


@router.post("/reset-password")
def reset_password(request: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset a user's password using the code sent to their email.
    """
    user = services.get_user_by_email(db, email=request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.reset_code or user.reset_code != request.code:
        raise HTTPException(status_code=400, detail="Invalid reset code")
    
    if user.reset_code_expires and datetime.utcnow() > user.reset_code_expires:
        raise HTTPException(status_code=400, detail="Reset code has expired. Please request a new one.")
    
    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    user.reset_code = None
    user.reset_code_expires = None
    db.commit()
    
    return {"message": "Password has been reset successfully. You can now log in with your new password."}

@router.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = services.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is verified (only for local auth)
    if user.provider == "local" and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email for the verification code.",
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "id": user.id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

class GoogleLoginRequest(BaseModel):
    token: str

@router.post("/google", response_model=schemas.Token)
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    try:
        # Verify the Google token

        id_info = id_token.verify_oauth2_token(
            request.token, 
            google_requests.Request(), 
            GOOGLE_CLIENT_ID
        )

        # lets print all the avaliable info here
        print("Google ID Info:", id_info)

        email = id_info['email']
        name = id_info.get('given_name', '')
        surname = id_info.get('family_name', '')
        picture = id_info.get('picture', None)
        
        # Check if user exists
        user = services.get_user_by_email(db, email=email)
        if not user:
            # Create new user
            import uuid
            new_user_id = str(uuid.uuid4())
            user_create = schemas.UserCreate(
                email=email,
                name=name,
                surname=surname,
                password="", # No password for Google users
                provider="google",
                avatar_url=picture
            )
            # We need to bypass the password requirement in UserCreate if we use it directly,
            # but UserCreate requires password.
            # Let's create a dict and pass it to create_user manually or adjust schema.
            # For now, I'll just pass a dummy password or handle it in create_user.
            # Actually, create_user takes UserCreate.
            # I should make password optional in UserCreate or have a separate UserCreateInternal.
            # I'll just pass a random string as password for now, it won't be used for login anyway since provider is google.
            user_create.password = str(uuid.uuid4()) 
            user = services.create_user(db, user_create, hashed_password=None)
            # Update provider and set Google users as verified but profile not completed
            user_db = services.get_user(db, user.id)
            user_db.provider = "google"
            user_db.is_verified = True  # Google users are auto-verified
            user_db.profile_completed = False  # Need to complete profile on first login
            db.commit()
            db.refresh(user_db)
            user = user_db
        else:
            # Update existing user's avatar if changed (optional, but good practice)
            if picture and user.avatar_url != picture:
                user.avatar_url = picture
                db.commit()
                db.refresh(user)

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "id": user.id}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Google token")
