"""Email worker."""

import os
import smtplib
from dotenv import load_dotenv
from icecream import ic

load_dotenv()

smtp_server = os.getenv("SMTP_SERVER")
smtp_port = int(os.getenv("SMTP_PORT"))
smtp_username = os.getenv("SMTP_USERNAME")
smtp_password = os.getenv("SMTP_PASSWORD")

sender = os.getenv("SENDER")
receiver = os.getenv("RECEIVER")


def send_email(changes):
    """Send email."""
    message = f"""\
    Subject: Changes detected\n
    Hi! There are some changes:\n
    {changes}
    """
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.login(smtp_username, smtp_password)
            server.sendmail(sender, receiver, message.encode("utf-8"))
        ic("Email sent")
    except Exception as e:
        ic(e)
