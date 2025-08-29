import os
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import HTTPException

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
DOMAIN = os.getenv("DOMAIN")


BOLD = "\033[1m"
END = "\033[0m"

def generate_verification_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def send_verification_email(to_email):
    sender_email = ADMIN_EMAIL
    sender_password = EMAIL_PASSWORD
    verification_code = generate_verification_code()

    subject = "Your Verification Code"
    body = f"Your verification code is: {verification_code}"

    # Create the email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    # Send the email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"Verification email sent to {to_email}")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Failed to send email")

    return verification_code  # Store this in DB or session for comparison

def trim_string(s: str, max_len: int = 20) -> str:
    return s[:max_len] if len(s) > max_len else s

def send_notification_email(to_email, latest_nis):
    sender_email = ADMIN_EMAIL
    sender_password = EMAIL_PASSWORD
    news_message =""
    for latest_ni in latest_nis:
        title = latest_ni["title"]
        published = latest_ni["published"]
        news_message = news_message + f"<p>{title} - {published}</p>"
    subject_text = trim_string(latest_nis[0]["title"])
    subject = f"You have new scrape: {subject_text}"
    html_body = f"""
    <html>
        <body>
    <h3 style="font-size:20px;">Here is the most recent news:</h3>
    <b style="font-size:14px;">{news_message}</b>
    Please login to our website at:
    {DOMAIN}
    </body>
</html>
"""

    # Create the email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(html_body, 'html'))

    # Send the email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"Verification email sent to {to_email}")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Failed to send email")
        return False

    return True