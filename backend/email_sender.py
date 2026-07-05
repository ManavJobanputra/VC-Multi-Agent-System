import logging

import requests

from config import RESEND_API_KEY, RESEND_FROM_EMAIL

logger = logging.getLogger(__name__)


def send_magic_link(email: str, link: str) -> None:
    """Send the login link to `email`. Without RESEND_API_KEY configured,
    logs the link instead - lets the whole auth flow be built and tested
    before a real email provider is wired up, same pattern used for the
    optional TAVILY_API_KEY elsewhere in this app."""
    if not RESEND_API_KEY:
        logger.info(f"[DEV MODE - no RESEND_API_KEY] Magic link for {email}: {link}")
        return

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={
                "from": RESEND_FROM_EMAIL,
                "to": [email],
                "subject": "Your VC Pitch Analyzer sign-in link",
                "html": (
                    f'<p>Click below to sign in:</p>'
                    f'<p><a href="{link}">{link}</a></p>'
                    f'<p>This link expires in 15 minutes.</p>'
                ),
            },
            timeout=10,
        )
        resp.raise_for_status()
        logger.info(f"Magic link emailed to {email}")
    except Exception as e:
        logger.error(f"Failed to send magic link email to {email}: {e}")
        raise
