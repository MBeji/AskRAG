"""
Email service for sending notifications.
"""

import logging
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending notifications."""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS
        self.from_email = settings.EMAIL_FROM
        self.from_name = settings.EMAIL_FROM_NAME
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Create SMTP session
            if self.use_tls:
                context = ssl.create_default_context()
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls(context=context)
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            
            # Login and send email
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            text = message.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False


# Email templates
def get_password_reset_email_template(username: str, reset_token: str) -> tuple[str, str]:
    """
    Get password reset email template.
    
    Args:
        username: User's username
        reset_token: Password reset token
        
    Returns:
        Tuple of (html_content, text_content)
    """
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Password Reset - AskRAG</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #2563eb;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .content {{
                background-color: #f8fafc;
                padding: 30px;
                border-radius: 0 0 8px 8px;
            }}
            .button {{
                display: inline-block;
                background-color: #2563eb;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 6px;
                margin: 20px 0;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e2e8f0;
                font-size: 14px;
                color: #64748b;
            }}
            .warning {{
                background-color: #fef3c7;
                border: 1px solid #f59e0b;
                color: #92400e;
                padding: 15px;
                border-radius: 6px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>AskRAG Password Reset</h1>
        </div>
        <div class="content">
            <h2>Hello {username},</h2>
            <p>We received a request to reset your password for your AskRAG account.</p>
            <p>Click the button below to reset your password:</p>
            
            <a href="{reset_url}" class="button">Reset Password</a>
            
            <div class="warning">
                <strong>Security Notice:</strong> This link will expire in 1 hour. If you didn't request this password reset, please ignore this email.
            </div>
            
            <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #2563eb;">{reset_url}</p>
            
            <div class="footer">
                <p>Best regards,<br>The AskRAG Team</p>
                <p><small>This is an automated email. Please do not reply to this email.</small></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    AskRAG Password Reset

    Hello {username},

    We received a request to reset your password for your AskRAG account.

    To reset your password, please visit the following link:
    {reset_url}

    This link will expire in 1 hour.

    If you didn't request this password reset, please ignore this email.

    Best regards,
    The AskRAG Team

    This is an automated email. Please do not reply to this email.
    """
    
    return html_content, text_content


def get_welcome_email_template(username: str, email: str) -> tuple[str, str]:
    """
    Get welcome email template for new users.
    
    Args:
        username: User's username
        email: User's email address
        
    Returns:
        Tuple of (html_content, text_content)
    """
    login_url = f"{settings.FRONTEND_URL}/login"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Welcome to AskRAG</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #10b981;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .content {{
                background-color: #f0fdf4;
                padding: 30px;
                border-radius: 0 0 8px 8px;
            }}
            .button {{
                display: inline-block;
                background-color: #10b981;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 6px;
                margin: 20px 0;
            }}
            .features {{
                background-color: white;
                padding: 20px;
                border-radius: 6px;
                margin: 20px 0;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e2e8f0;
                font-size: 14px;
                color: #64748b;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Welcome to AskRAG!</h1>
        </div>
        <div class="content">
            <h2>Hello {username},</h2>
            <p>Welcome to AskRAG! Your account has been successfully created.</p>
            
            <div class="features">
                <h3>What you can do with AskRAG:</h3>
                <ul>
                    <li>📄 Upload and manage your documents</li>
                    <li>🤖 Ask questions about your documents using AI</li>
                    <li>🔍 Get intelligent, context-aware answers</li>
                    <li>📊 Track your document usage and analytics</li>
                </ul>
            </div>
            
            <p>Ready to get started? Click the button below to log in:</p>
            
            <a href="{login_url}" class="button">Log In to AskRAG</a>
            
            <p>Your account details:</p>
            <ul>
                <li><strong>Username:</strong> {username}</li>
                <li><strong>Email:</strong> {email}</li>
            </ul>
            
            <div class="footer">
                <p>Best regards,<br>The AskRAG Team</p>
                <p><small>If you have any questions, feel free to contact our support team.</small></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Welcome to AskRAG!

    Hello {username},

    Welcome to AskRAG! Your account has been successfully created.

    What you can do with AskRAG:
    - Upload and manage your documents
    - Ask questions about your documents using AI
    - Get intelligent, context-aware answers
    - Track your document usage and analytics

    Your account details:
    - Username: {username}
    - Email: {email}

    To get started, please visit: {login_url}

    Best regards,
    The AskRAG Team

    If you have any questions, feel free to contact our support team.
    """
    
    return html_content, text_content


# Global email service instance
email_service = EmailService()


async def send_password_reset_email(email: str, username: str, reset_token: str) -> bool:
    """
    Send password reset email.
    
    Args:
        email: User's email address
        username: User's username
        reset_token: Password reset token
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    if not settings.SEND_EMAILS:
        logger.info(f"Email sending disabled. Would send password reset to {email}")
        return True
    
    html_content, text_content = get_password_reset_email_template(username, reset_token)
    
    return await email_service.send_email(
        to_email=email,
        subject="AskRAG Password Reset",
        html_content=html_content,
        text_content=text_content
    )


async def send_welcome_email(email: str, username: str) -> bool:
    """
    Send welcome email to new users.
    
    Args:
        email: User's email address
        username: User's username
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    if not settings.SEND_EMAILS:
        logger.info(f"Email sending disabled. Would send welcome email to {email}")
        return True
    
    html_content, text_content = get_welcome_email_template(username, email)
    
    return await email_service.send_email(
        to_email=email,
        subject="Welcome to AskRAG!",
        html_content=html_content,
        text_content=text_content
    )
