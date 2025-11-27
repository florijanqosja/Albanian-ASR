"""
Mail Service for sending emails using the AhaSend API.
Handles verification codes, welcome emails, and password reset emails.
"""

import os
import random
import string
import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)

# Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
MAIL_API_KEY = os.getenv("MAIL_API_KEY")
MAIL_API_URL = os.getenv("MAIL_API_URL", "https://api.ahasend.com")
MAIL_ACCOUNT_ID = os.getenv("AHASEND_ACCOUNT_ID")
MAIL_FROM_EMAIL = os.getenv("MAIL_FROM_EMAIL", "noreply@dibraspeaks.com")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "DibraSpeaks")
APP_URL = os.getenv("NEXTAUTH_URL", "http://localhost:3000")


def is_production() -> bool:
    """Check if running in production environment."""
    return ENVIRONMENT.lower() == "production"


def validate_mail_config() -> None:
    """
    Validate mail configuration.
    Raises RuntimeError if in production and required variables are missing.
    """
    if is_production():
        missing = []
        if not MAIL_API_KEY:
            missing.append("MAIL_API_KEY")
        if not MAIL_ACCOUNT_ID:
            missing.append("AHASEND_ACCOUNT_ID")
        if not MAIL_FROM_EMAIL:
            missing.append("MAIL_FROM_EMAIL")
        
        if missing:
            raise RuntimeError(
                f"Production environment requires email configuration. "
                f"Missing variables: {', '.join(missing)}"
            )


# Validate on module load in production
if is_production():
    validate_mail_config()

# Brand colors matching the dashboard theme
BRAND_PRIMARY = "#A64D4A"  # Soft Red
BRAND_TEXT = "#404040"  # Neutral Dark Gray
BRAND_BACKGROUND = "#ffffff"  # White
BRAND_ACCENT = "#FFE4E6"  # Soft Rose
BRAND_SECONDARY = "#F3F4F6"  # Light Gray
BRAND_BORDER = "#FECACA"  # Light Red


def generate_verification_code(length: int = 6) -> str:
    """Generate a random numeric verification code."""
    return ''.join(random.choices(string.digits, k=length))


def _get_base_email_template(content: str, title: str) -> str:
    """Get the base HTML email template with DibraSpeaks branding."""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Khula:wght@400;600;700;800&display=swap');
    </style>
</head>
<body style="margin: 0; padding: 0; font-family: 'Khula', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: {BRAND_SECONDARY};">
    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: {BRAND_SECONDARY};">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: {BRAND_BACKGROUND}; border-radius: 16px; border: 1px solid {BRAND_BORDER}; box-shadow: 0 20px 40px -10px rgba(0,0,0,0.05);">
                    <!-- Header -->
                    <tr>
                        <td align="center" style="padding: 40px 40px 20px;">
                            <div style="width: 80px; height: 80px; margin-bottom: 24px;">
                                <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <circle cx="50" cy="50" r="45" fill="{BRAND_ACCENT}"/>
                                    <path d="M30 65 L50 35 L70 65" stroke="{BRAND_PRIMARY}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                                    <circle cx="50" cy="55" r="8" fill="{BRAND_PRIMARY}"/>
                                </svg>
                            </div>
                            <p style="margin: 0 0 12px; font-size: 18px; font-weight: 700; letter-spacing: 2px; color: {BRAND_PRIMARY};">DIBRASPEAKS</p>
                            <h1 style="margin: 0; font-size: 28px; font-weight: 800; color: {BRAND_TEXT};">{title}</h1>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 20px 40px 40px;">
                            {content}
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td align="center" style="padding: 30px 40px; background-color: {BRAND_SECONDARY}; border-radius: 0 0 16px 16px;">
                            <p style="margin: 0 0 10px; font-size: 14px; color: #6B7280;">
                                This email was sent by DibraSpeaks
                            </p>
                            <p style="margin: 0; font-size: 12px; color: #9CA3AF;">
                                © 2025 DibraSpeaks. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def _get_verification_email_content(code: str, name: Optional[str] = None) -> str:
    """Generate the verification email content."""
    greeting = f"Hi {name}," if name else "Hello,"
    return f"""
        <p style="margin: 0 0 20px; font-size: 16px; color: {BRAND_TEXT}; line-height: 1.6;">
            {greeting}
        </p>
        <p style="margin: 0 0 20px; font-size: 16px; color: {BRAND_TEXT}; line-height: 1.6;">
            Thanks for signing up for DibraSpeaks! Please use the verification code below to confirm your email address.
        </p>
        <div style="text-align: center; margin: 30px 0;">
            <div style="display: inline-block; background-color: {BRAND_ACCENT}; padding: 20px 40px; border-radius: 12px; border: 2px dashed {BRAND_PRIMARY};">
                <span style="font-size: 36px; font-weight: 800; letter-spacing: 8px; color: {BRAND_PRIMARY};">{code}</span>
            </div>
        </div>
        <p style="margin: 0 0 20px; font-size: 14px; color: #6B7280; line-height: 1.6;">
            This code will expire in <strong>15 minutes</strong>. If you didn't create an account with DibraSpeaks, you can safely ignore this email.
        </p>
"""


def _get_welcome_email_content(name: Optional[str] = None) -> str:
    """Generate the welcome email content."""
    greeting = f"Welcome aboard, {name}!" if name else "Welcome aboard!"
    return f"""
        <p style="margin: 0 0 20px; font-size: 16px; color: {BRAND_TEXT}; line-height: 1.6;">
            {greeting}
        </p>
        <p style="margin: 0 0 20px; font-size: 16px; color: {BRAND_TEXT}; line-height: 1.6;">
            Your email has been verified and your DibraSpeaks account is now active. You're now part of our community helping to build Albanian speech recognition technology!
        </p>
        <p style="margin: 0 0 20px; font-size: 16px; color: {BRAND_TEXT}; line-height: 1.6;">
            Here's what you can do next:
        </p>
        <ul style="margin: 0 0 20px; padding-left: 20px; font-size: 16px; color: {BRAND_TEXT}; line-height: 1.8;">
            <li>Complete your profile</li>
            <li>Start validating audio transcriptions</li>
            <li>Contribute to building Albanian ASR</li>
        </ul>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{APP_URL}" style="display: inline-block; background-color: {BRAND_PRIMARY}; color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: 700; font-size: 16px; box-shadow: 0 4px 14px 0 rgba(166, 77, 74, 0.39);">
                Get Started
            </a>
        </div>
"""


def _get_password_reset_email_content(code: str, name: Optional[str] = None) -> str:
    """Generate the password reset email content."""
    greeting = f"Hi {name}," if name else "Hello,"
    return f"""
        <p style="margin: 0 0 20px; font-size: 16px; color: {BRAND_TEXT}; line-height: 1.6;">
            {greeting}
        </p>
        <p style="margin: 0 0 20px; font-size: 16px; color: {BRAND_TEXT}; line-height: 1.6;">
            We received a request to reset your password. Use the code below to set a new password for your account.
        </p>
        <div style="text-align: center; margin: 30px 0;">
            <div style="display: inline-block; background-color: {BRAND_ACCENT}; padding: 20px 40px; border-radius: 12px; border: 2px dashed {BRAND_PRIMARY};">
                <span style="font-size: 36px; font-weight: 800; letter-spacing: 8px; color: {BRAND_PRIMARY};">{code}</span>
            </div>
        </div>
        <p style="margin: 0 0 20px; font-size: 14px; color: #6B7280; line-height: 1.6;">
            This code will expire in <strong>15 minutes</strong>. If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.
        </p>
"""


def _send_email(to_email: str, to_name: Optional[str], subject: str, html_content: str) -> bool:
    """
    Send an email using the AhaSend API.
    In local environment, logs the email instead of sending.
    Returns True if successful, False otherwise.
    """
    # In local environment, just log and return success
    if not is_production():
        logger.info(f"[LOCAL MODE] Would send email to {to_email}: {subject}")
        logger.debug(f"[LOCAL MODE] Email content preview: {html_content[:200]}...")
        return True
    
    if not MAIL_API_KEY:
        logger.error("MAIL_API_KEY is not configured")
        return False
    
    if not MAIL_ACCOUNT_ID:
        logger.error("MAIL_ACCOUNT_ID is not configured")
        return False

    # AhaSend API v2 endpoint
    url = f"{MAIL_API_URL}/v2/accounts/{MAIL_ACCOUNT_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {MAIL_API_KEY}",
        "Content-Type": "application/json"
    }

    # Build recipient object
    recipient = {"email": to_email}
    if to_name:
        recipient["name"] = to_name

    payload = {
        "from": {
            "email": MAIL_FROM_EMAIL,
            "name": MAIL_FROM_NAME
        },
        "recipients": [recipient],
        "subject": subject,
        "html_content": html_content,
        "text_content": "Please view this email in an HTML-compatible email client."
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201, 202]:
            logger.info(f"Email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"Failed to send email: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Email sending failed: {e}")
        return False


def send_verification_email(to_email: str, code: str, name: Optional[str] = None) -> bool:
    """Send a verification code email."""
    content = _get_verification_email_content(code, name)
    html = _get_base_email_template(content, "Verify Your Email")
    return _send_email(to_email, name, "Verify your DibraSpeaks account", html)


def send_welcome_email(to_email: str, name: Optional[str] = None) -> bool:
    """Send a welcome email after successful verification."""
    content = _get_welcome_email_content(name)
    html = _get_base_email_template(content, "Welcome to DibraSpeaks!")
    return _send_email(to_email, name, "Welcome to DibraSpeaks!", html)


def send_password_reset_email(to_email: str, code: str, name: Optional[str] = None) -> bool:
    """Send a password reset code email."""
    content = _get_password_reset_email_content(code, name)
    html = _get_base_email_template(content, "Reset Your Password")
    return _send_email(to_email, name, "Reset your DibraSpeaks password", html)
