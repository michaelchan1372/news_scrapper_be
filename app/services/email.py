import os
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import HTTPException

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

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