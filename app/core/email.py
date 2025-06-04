import smtplib
from email.mime.text import MIMEText

from app.core.configs import settings


def send_email(to: str, subject: str, body: str):
    from_address = settings.EMAIL
    password = settings.EMAIL_PASSWORD

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_address, password)
        server.send_message(msg)
