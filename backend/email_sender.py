import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from config import (
    SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL, SMTP_USE_TLS,
    RESEND_API_KEY, RESEND_FROM_EMAIL,
)

logger = logging.getLogger(__name__)

SUBJECT = "Your VC Pitch Analyzer sign-in link"


def _html_body(link: str) -> str:
    return (
        f'<p>Click below to sign in:</p>'
        f'<p><a href="{link}">{link}</a></p>'
        f'<p>This link expires in 15 minutes.</p>'
    )


def _send_via_smtp(email: str, link: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = SUBJECT
    msg["From"] = SMTP_FROM_EMAIL
    msg["To"] = email
    msg.attach(MIMEText(_html_body(link), "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
        if SMTP_USE_TLS:
            server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM_EMAIL, [email], msg.as_string())

    logger.info(f"Magic link emailed to {email} via SMTP ({SMTP_HOST})")


def _send_via_resend(email: str, link: str) -> None:
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
        json={
            "from": RESEND_FROM_EMAIL,
            "to": [email],
            "subject": SUBJECT,
            "html": _html_body(link),
        },
        timeout=10,
    )
    resp.raise_for_status()
    logger.info(f"Magic link emailed to {email} via Resend")


def send_magic_link(email: str, link: str) -> None:
    """Send the login link to `email`. Tries SMTP first (if SMTP_HOST is
    set), then Resend (if RESEND_API_KEY is set), then logs the link to
    the console - fine for local dev/testing, not for real users."""
    if SMTP_HOST:
        try:
            _send_via_smtp(email, link)
            return
        except Exception as e:
            logger.error(f"SMTP send to {email} failed: {e}")
            raise

    if RESEND_API_KEY:
        try:
            _send_via_resend(email, link)
            return
        except Exception as e:
            logger.error(f"Resend send to {email} failed: {e}")
            raise

    logger.info(f"[DEV MODE - no SMTP_HOST or RESEND_API_KEY configured] Magic link for {email}: {link}")
