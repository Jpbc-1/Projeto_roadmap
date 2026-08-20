import logging

logger = logging.getLogger(__name__)

async def send_verification_email(email: str, token: str):
    """
    STUB: Simula o envio de um e-mail. 
    No futuro, integrar com Resend, SendGrid ou AWS SES aqui.
    """
    logger.info(f"Verification email sent to {email}")