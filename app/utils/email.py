# app/utils/email.py
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str) -> None:
    """
    Send a plain-text email using SMTP settings from config.py
    Works with BackgroundTasks (non-blocking).
    """
    msg = MIMEMultipart()
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(
            settings.SMTP_SERVER,
            int(settings.SMTP_PORT),
            timeout=30
        )
        server.ehlo()

        if settings.SMTP_USE_TLS:
            server.starttls()
            server.ehlo()

        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

        server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())
        server.quit()

        logger.info(f"✅ Email sent successfully to {to_email}")

    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {str(e)}", exc_info=True)
        # We do NOT raise exception here because it's called from BackgroundTasks