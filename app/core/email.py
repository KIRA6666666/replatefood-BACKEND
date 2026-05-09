import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


async def send_verification_email(to_email: str, otp_code: str) -> None:
    html = f"""
    <html><body style="font-family:sans-serif;color:#1a1a1a;max-width:480px;margin:auto;padding:32px">
      <h2 style="color:#F47521">Vérifiez votre adresse e-mail</h2>
      <p>Merci de vous être inscrit sur Mealate. Utilisez le code ci-dessous pour activer votre compte.</p>
      <div style="margin:32px 0;text-align:center">
        <span style="display:inline-block;background:#FFF4EC;border:2px solid #F47521;border-radius:12px;
                     padding:16px 40px;font-size:36px;font-weight:700;letter-spacing:10px;color:#F47521">
          {otp_code}
        </span>
      </div>
      <p style="font-size:13px;color:#666">
        Ce code expire dans <strong>15 minutes</strong>.<br>
        Si vous n'êtes pas à l'origine de cette inscription, ignorez cet e-mail.
      </p>
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
      <p style="font-size:12px;color:#999">Mealate — Ne pas répondre à cet e-mail.</p>
    </body></html>
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = "Votre code d'activation Mealate"
    message["From"] = settings.SMTP_FROM
    message["To"] = to_email
    message.attach(MIMEText(html, "html"))

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )


async def send_reset_email(to_email: str, otp_code: str) -> None:
    html = f"""
    <html><body style="font-family:sans-serif;color:#1a1a1a;max-width:480px;margin:auto;padding:32px">
      <h2 style="color:#F47521">Réinitialisation de votre mot de passe</h2>
      <p>Utilisez le code ci-dessous pour réinitialiser votre mot de passe.</p>
      <div style="margin:32px 0;text-align:center">
        <span style="display:inline-block;background:#FFF4EC;border:2px solid #F47521;border-radius:12px;
                     padding:16px 40px;font-size:36px;font-weight:700;letter-spacing:10px;color:#F47521">
          {otp_code}
        </span>
      </div>
      <p style="font-size:13px;color:#666">
        Ce code expire dans <strong>15 minutes</strong>.<br>
        Si vous n'êtes pas à l'origine de cette demande, ignorez cet e-mail.
      </p>
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
      <p style="font-size:12px;color:#999">Mealate — Ne pas répondre à cet e-mail.</p>
    </body></html>
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = "Votre code de réinitialisation Mealate"
    message["From"] = settings.SMTP_FROM
    message["To"] = to_email
    message.attach(MIMEText(html, "html"))

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )
