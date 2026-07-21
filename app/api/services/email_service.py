import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


async def send_staff_invitation(email: str, first_name: str, token: str):
    """Send staff invitation email with password setup link."""
    
    subject = "Welcome to Kings Cut Addis - Set Your Password"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f8f8f8; padding: 20px;">
        <div style="max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h1 style="color: #C9A84C; text-align: center; margin-bottom: 20px;">KINGS CUT ADDIS</h1>
            <h2 style="color: #1a1a1a; text-align: center; margin-bottom: 30px;">Welcome, {first_name}!</h2>
            <p style="color: #666666; line-height: 1.6;">
                You have been added as a staff member at Kings Cut Addis. 
                Please click the button below to set your password and access the admin dashboard.
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="http://localhost:5174/set-password?token={token}" 
                   style="background: linear-gradient(180deg, #C9A84C, #B8860B); 
                          color: white; 
                          padding: 15px 30px; 
                          text-decoration: none; 
                          border-radius: 5px; 
                          font-weight: bold;">
                    Set Your Password
                </a>
            </div>
            <p style="color: #999999; font-size: 12px; text-align: center;">
                This link will expire in 24 hours. If you didn't expect this email, please ignore it.
            </p>
        </div>
    </body>
    </html>
    """
    
    message = MIMEMultipart("alternative")
    message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    message["To"] = email
    message["Subject"] = subject
    message.attach(MIMEText(html_content, "html"))
    
    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )