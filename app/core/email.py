from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from app.core.config import settings # <--- Import your centralized settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True # Set to True in production for HIPAA security
)

class EmailService:
    @staticmethod
    async def send_verification_email(email: str, token: str):
        # Use the FRONTEND_URL from config
        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        
        message = MessageSchema(
            subject="Verify your BTT Account",
            recipients=[email],
            body=f"Welcome to BTT. Please verify your email: {verify_url}",
            subtype=MessageType.html
        )
        fm = FastMail(conf)
        await fm.send_message(message)

    @staticmethod
    async def send_password_reset_email(email: str, token: str):
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        message = MessageSchema(
            subject="Password Reset Request",
            recipients=[email],
            body=f"Click here to reset your password: {reset_url}",
            subtype=MessageType.html
        )
        fm = FastMail(conf)
        await fm.send_message(message)