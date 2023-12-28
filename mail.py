"""Email worker."""

import logging
import os
import smtplib
import ssl
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv
from icecream import ic

load_dotenv()

smtp_server = os.getenv("SMTP_SERVER")
smtp_port = int(os.getenv("SMTP_PORT"))
smtp_username = os.getenv("SMTP_USERNAME")
smtp_password = os.getenv("SMTP_PASSWORD")

sender = os.getenv("SENDER")
receiver = os.getenv("RECEIVER")


def send_email(subject: str, project_name: str = None, json_file_path=None):
    """Send email."""
    m = MIMEMultipart()
    m.add_header("from", sender)
    m.add_header("to", receiver)
    m.add_header("subject", subject)

    # Create email body as an unpacked dicts
    # letter_lines = []
    # if changes:
    #     for item in changes:
    #         for key, value in item.items():
    #             letter_lines.append(f"{key}: {value}")
    #         letter_lines.append("*" * 20)
    #     email_str = "\n".join(letter_lines)
    #     m.set_payload(payload=email_str, charset="utf-8")

    if json_file_path:
        with open(json_file_path, "rb") as file:
            attachment = MIMEApplication(file.read(), _subtype="json")
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=f"{project_name}_{datetime.now()}.json",
            )
            m.attach(attachment)

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
