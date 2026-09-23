import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_verification_email(to_email: str, code: str, full_name: str = "") -> bool:
    """
    Sends a 6-digit verification code to the recipient's email using SMTP.
    If SMTP environment variables are not configured, logs the code to backend console.
    """
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip() or os.getenv("EMAIL_FROM", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip() or os.getenv("EMAIL_PASSWORD", "").strip()
    sender_email = os.getenv("EMAIL_FROM", "").strip() or smtp_user or "noreply@lingualearn.com"

    subject = "Your NeoLearner Email Verification Code"
    recipient_name = full_name if full_name else "Learner"

    html_content = f"""
    <!DOCTYPE html>
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

    if smtp_host and smtp_user and smtp_password:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"NeoLearner <{sender_email}>"
            msg["To"] = to_email

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                server.starttls()
            
            server.login(smtp_user, smtp_password)
            server.sendmail(sender_email, [to_email], msg.as_string())
            server.quit()
            print(f"[EMAIL SERVICE] Verification email successfully sent to {to_email}")
            return True
        except Exception as e:
            print(f"[EMAIL SERVICE ERROR] Failed to send email via SMTP to {to_email}: {e}")
            print(f"[EMAIL SERVICE FALLBACK] Verification code for {to_email} is: {code}")
            return False
    else:
        print(f"[EMAIL SERVICE NOTICE] SMTP credentials not fully configured in environment.")
        print(f"[EMAIL SERVICE FALLBACK] Verification code sent to {to_email}: {code}")
        return True
