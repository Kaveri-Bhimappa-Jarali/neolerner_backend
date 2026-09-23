import os
import json
import ssl
import smtplib
import urllib.request
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr
from dotenv import load_dotenv

load_dotenv()

def send_verification_email(to_email: str, code: str, full_name: str = "") -> bool:
    """
    Sends a 6-digit verification code to the recipient's target email address.
    Supports SMTP (Gmail, Outlook, custom SMTP), Resend API, and SendGrid API.
    """
    to_email = to_email.strip().lower()
    recipient_name = full_name.strip() if full_name and full_name.strip() else "Learner"
    subject = "Your NeoLearner Email Verification Code"

    # HTML and Plaintext email templates
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Email Verification</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px;">
  <div style="max-width: 520px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; padding: 32px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0;">
    <div style="text-align: center; margin-bottom: 24px;">
      <div style="display: inline-block; background: linear-gradient(135deg, #10b981, #3b82f6); padding: 12px 20px; border-radius: 12px; color: #ffffff; font-weight: bold; font-size: 20px;">
        NeoLearner
      </div>
    </div>
    
    <h2 style="color: #0f172a; font-size: 22px; margin-bottom: 12px; text-align: center;">Verify Your Email Address</h2>
    <p style="color: #475569; font-size: 15px; line-height: 1.6; margin-bottom: 24px;">
      Hello <strong>{recipient_name}</strong>,<br>
      Thank you for signing up with NeoLearner! Please use the 6-digit verification code below to complete your account setup:
    </p>
    
    <div style="text-align: center; margin: 28px 0;">
      <span style="display: inline-block; background-color: #f1f5f9; color: #10b981; font-size: 32px; font-weight: 800; letter-spacing: 8px; padding: 16px 32px; border-radius: 12px; border: 2px dashed #10b981;">
        {code}
      </span>
    </div>
    
    <p style="color: #64748b; font-size: 13px; text-align: center; margin-top: 24px;">
      This code is valid for your current session. If you did not request this code, please ignore this email.
    </p>
  </div>
</body>
</html>
"""

    text_content = f"Hello {recipient_name},\n\nYour NeoLearner email verification code is: {code}\n\nThank you!"

    # 1. Check for HTTP API Email Services (Resend, SendGrid)
    resend_api_key = os.getenv("RESEND_API_KEY", "").strip()
    if resend_api_key:
        try:
            sender_addr = os.getenv("EMAIL_FROM", "").strip() or "onboarding@resend.dev"
            payload = json.dumps({
                "from": sender_addr if "@" in sender_addr else "onboarding@resend.dev",
                "to": [to_email],
                "subject": subject,
                "html": html_content,
                "text": text_content
            }).encode("utf-8")
            
            req = urllib.request.Request("https://api.resend.com/emails", data=payload, headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status in (200, 201, 202):
                    print(f"[EMAIL SERVICE] Verification email dispatched via Resend to {to_email}")
                    return True
        except Exception as e:
            print(f"[EMAIL SERVICE ERROR] Resend dispatch failed: {e}")

    sendgrid_api_key = os.getenv("SENDGRID_API_KEY", "").strip()
    if sendgrid_api_key:
        try:
            sender_addr = os.getenv("EMAIL_FROM", "").strip() or "noreply@lingualearn.com"
            payload = json.dumps({
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": sender_addr},
                "subject": subject,
                "content": [
                    {"type": "text/plain", "value": text_content},
                    {"type": "text/html", "value": html_content}
                ]
            }).encode("utf-8")

            req = urllib.request.Request("https://api.sendgrid.com/v3/mail/send", data=payload, headers={
                "Authorization": f"Bearer {sendgrid_api_key}",
                "Content-Type": "application/json"
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status in (200, 201, 202):
                    print(f"[EMAIL SERVICE] Verification email dispatched via SendGrid to {to_email}")
                    return True
        except Exception as e:
            print(f"[EMAIL SERVICE ERROR] SendGrid dispatch failed: {e}")

    # 2. Extract SMTP Environment Variables
    smtp_host = (
        os.getenv("SMTP_HOST", "").strip()
        or os.getenv("EMAIL_HOST", "").strip()
        or os.getenv("MAIL_SERVER", "").strip()
        or os.getenv("MAIL_HOST", "").strip()
        or os.getenv("SMTP_SERVER", "").strip()
    )
    
    smtp_port_raw = (
        os.getenv("SMTP_PORT", "").strip()
        or os.getenv("EMAIL_PORT", "").strip()
        or os.getenv("MAIL_PORT", "").strip()
        or "587"
    )
    try:
        smtp_port = int(smtp_port_raw)
    except ValueError:
        smtp_port = 587

    smtp_user = (
        os.getenv("SMTP_USER", "").strip()
        or os.getenv("SMTP_USERNAME", "").strip()
        or os.getenv("EMAIL_HOST_USER", "").strip()
        or os.getenv("EMAIL_USER", "").strip()
        or os.getenv("MAIL_USERNAME", "").strip()
        or os.getenv("EMAIL_FROM", "").strip()
    )

    smtp_password = (
        os.getenv("SMTP_PASSWORD", "").strip()
        or os.getenv("SMTP_PASS", "").strip()
        or os.getenv("EMAIL_HOST_PASSWORD", "").strip()
        or os.getenv("EMAIL_PASSWORD", "").strip()
        or os.getenv("MAIL_PASSWORD", "").strip()
    )

    raw_sender = (
        os.getenv("EMAIL_FROM", "").strip()
        or os.getenv("DEFAULT_FROM_EMAIL", "").strip()
        or smtp_user
        or "noreply@lingualearn.com"
    )

    # Clean sender address formatting
    _, parsed_email = parseaddr(raw_sender)
    clean_sender_email = parsed_email if parsed_email and "@" in parsed_email else (smtp_user if "@" in smtp_user else "noreply@lingualearn.com")
    formatted_from_header = formataddr(("NeoLearner", clean_sender_email))

    if smtp_host and smtp_user and smtp_password:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = formatted_from_header
            msg["To"] = to_email

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            ssl_context = ssl.create_default_context()

            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, context=ssl_context, timeout=15)
                server.ehlo()
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
                server.ehlo()
                if server.has_extn("starttls"):
                    server.starttls(context=ssl_context)
                    server.ehlo()

            server.login(smtp_user, smtp_password)
            server.sendmail(clean_sender_email, [to_email], msg.as_string())
            server.quit()
            print(f"[EMAIL SERVICE] Verification email successfully sent via SMTP to {to_email}")
            return True
        except Exception as e:
            print(f"[EMAIL SERVICE ERROR] Failed to send email via SMTP to {to_email}: {e}")
            print(f"[EMAIL SERVICE FALLBACK] Verification code for {to_email} is: {code}")
            return False
    else:
        print(f"[EMAIL SERVICE NOTICE] SMTP credentials not fully configured in environment variables.")
        print(f"[EMAIL SERVICE FALLBACK] Verification code for {to_email}: {code}")
        return True
