"""Email worker."""

import logging
import os
import smtplib
import ssl
from email import message

from dotenv import load_dotenv
from icecream import ic

load_dotenv()

smtp_server = os.getenv("SMTP_SERVER")
smtp_port = int(os.getenv("SMTP_PORT"))
smtp_username = os.getenv("SMTP_USERNAME")
smtp_password = os.getenv("SMTP_PASSWORD")

sender = os.getenv("SENDER")
receiver = os.getenv("RECEIVER")


m = message.Message()


def send_email(subject: str, changes=None):
    """Send email."""
    m.add_header("from", sender)
    m.add_header("to", receiver)
    m.add_header("subject", subject)
    m.set_payload(payload=str(changes), charset="utf-8")

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(
            smtp_server, smtp_port, context=context, timeout=20
        ) as server:
            server.login(smtp_username, smtp_password)
            server.sendmail(sender, receiver, m.as_string())
        ic("Email sent")
    except Exception as e:
        logging.error(e)
        ic(e)
