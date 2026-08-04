"""
Email notification service for TaskHub.
Uses aiosmtplib for async email sending via Gmail SMTP.
Graceful degradation: logs warning if SMTP is not configured.
"""
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


def _is_smtp_configured() -> bool:
    """Check if SMTP credentials are properly configured."""
    return bool(settings.SMTP_USER and settings.SMTP_PASSWORD)


async def send_task_assignment_email(
    to_email: str,
    to_name: str,
    task_title: str,
    project_name: str,
    assigner_name: str,
) -> None:
    """
    Send an email notification when a user is assigned a task.
    
    Args:
        to_email: Recipient's email address
        to_name: Recipient's full name
        task_title: Title of the assigned task
        project_name: Name of the project containing the task
        assigner_name: Name of the user who assigned the task
    """
    if not _is_smtp_configured():
        logger.warning(
            f"SMTP not configured. Skipping email to {to_email} "
            f"for task '{task_title}'"
        )
        return

    subject = f"[TaskHub] Bạn được gán task mới: {task_title}"

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">🎯 TaskHub</h1>
            </div>
            <div style="background: #f9f9f9; padding: 20px; border-radius: 0 0 10px 10px;
                        border: 1px solid #eee; border-top: none;">
                <p>Xin chào <strong>{to_name}</strong>,</p>
                <p>Bạn vừa được <strong>{assigner_name}</strong> gán một task mới:</p>
                <div style="background: white; padding: 15px; border-radius: 8px; 
                            border-left: 4px solid #667eea; margin: 15px 0;">
                    <p style="margin: 5px 0;"><strong>📋 Task:</strong> {task_title}</p>
                    <p style="margin: 5px 0;"><strong>📂 Project:</strong> {project_name}</p>
                    <p style="margin: 5px 0;"><strong>👤 Assigned by:</strong> {assigner_name}</p>
                </div>
                <p>Hãy đăng nhập vào TaskHub để xem chi tiết và bắt đầu làm việc.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #999;">
                    Email này được gửi tự động từ hệ thống TaskHub.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = to_email

    # Plain text fallback
    text_body = (
        f"Xin chào {to_name},\n\n"
        f"Bạn vừa được {assigner_name} gán task mới: {task_title}\n"
        f"Project: {project_name}\n\n"
        f"Hãy đăng nhập vào TaskHub để xem chi tiết.\n"
    )
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.SMTP_TLS,
        )
        logger.info(f"Email sent to {to_email} for task '{task_title}'")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
