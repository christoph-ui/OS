"""
Email service for transactional emails
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, List
from pathlib import Path

from ..config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending transactional emails"""

    @classmethod
    async def send_email(
        cls,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        attachments: Optional[List[tuple[str, bytes]]] = None
    ) -> bool:
        """
        Send an email

        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML body
            body_text: Plain text body (optional)
            attachments: List of (filename, content) tuples

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
            msg["To"] = to_email

            # Add text part
            if body_text:
                msg.attach(MIMEText(body_text, "plain", "utf-8"))

            # Add HTML part
            msg.attach(MIMEText(body_html, "html", "utf-8"))

            # Add attachments
            if attachments:
                for filename, content in attachments:
                    part = MIMEApplication(content, Name=filename)
                    part["Content-Disposition"] = f'attachment; filename="{filename}"'
                    msg.attach(part)

            # Send via SMTP
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    @classmethod
    async def send_verification_email(
        cls,
        email: str,
        name: str,
        token: str
    ) -> bool:
        """Send email verification email"""

        verification_url = f"{settings.website_url}/signup/verify?token={token}"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #faf9f5; background: #141413; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .header h1 {{ color: #d97757; font-size: 32px; margin: 0; }}
                .content {{ background: #1a1a19; padding: 30px; border-radius: 8px; }}
                .button {{ display: inline-block; padding: 14px 32px; background: #d97757; color: #fff; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #888; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>0711</h1>
                </div>
                <div class="content">
                    <h2 style="color: #faf9f5;">Willkommen bei 0711, {name}!</h2>
                    <p>Vielen Dank für Ihre Registrierung. Bitte bestätigen Sie Ihre E-Mail-Adresse, um fortzufahren.</p>
                    <p style="text-align: center;">
                        <a href="{verification_url}" class="button">E-Mail bestätigen</a>
                    </p>
                    <p style="color: #888; font-size: 14px;">
                        Oder kopieren Sie diesen Link in Ihren Browser:<br>
                        {verification_url}
                    </p>
                    <p style="color: #888; font-size: 14px; margin-top: 30px;">
                        Der Link ist 24 Stunden gültig.
                    </p>
                </div>
                <div class="footer">
                    <p>© 2024 0711 Intelligence GmbH | Stuttgart, Deutschland</p>
                </div>
            </div>
        </body>
        </html>
        """

        return await cls.send_email(
            to_email=email,
            subject="Bestätigen Sie Ihre E-Mail-Adresse",
            body_html=html
        )

    @classmethod
    async def send_invoice(
        cls,
        email: str,
        invoice,
        pdf_path: str
    ) -> bool:
        """Send invoice email with PDF attachment"""

        # Read PDF
        with open(pdf_path, "rb") as f:
            pdf_content = f.read()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #faf9f5; background: #141413; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
                .content {{ background: #1a1a19; padding: 30px; border-radius: 8px; }}
                .invoice-details {{ background: #2a2a29; padding: 20px; border-radius: 6px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #888; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
                    <h2 style="color: #d97757;">Ihre Rechnung von 0711</h2>
                    <p>Anbei erhalten Sie Ihre Rechnung im PDF-Format.</p>
                    <div class="invoice-details">
                        <p><strong>Rechnungsnummer:</strong> {invoice.invoice_number}</p>
                        <p><strong>Betrag:</strong> €{invoice.total_cents / 100:.2f}</p>
                        <p><strong>Fällig am:</strong> {invoice.due_date.strftime('%d.%m.%Y')}</p>
                    </div>
                    <p>Zahlungsziel: 30 Tage netto</p>
                    <p style="color: #888; font-size: 14px; margin-top: 30px;">
                        Bei Fragen zu Ihrer Rechnung wenden Sie sich bitte an buchhaltung@0711.io
                    </p>
                </div>
                <div class="footer">
                    <p>© 2024 0711 Intelligence GmbH | Stuttgart, Deutschland</p>
                </div>
            </div>
        </body>
        </html>
        """

        return await cls.send_email(
            to_email=email,
            subject=f"Rechnung {invoice.invoice_number}",
            body_html=html,
            attachments=[(f"{invoice.invoice_number}.pdf", pdf_content)]
        )

    @classmethod
    async def send_welcome_email(
        cls,
        email: str,
        name: str,
        license_key: str
    ) -> bool:
        """Send welcome email after signup completion"""

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #faf9f5; background: #141413; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
                .content {{ background: #1a1a19; padding: 30px; border-radius: 8px; }}
                .license {{ background: #2a2a29; padding: 15px; border-radius: 6px; font-family: 'Courier New', monospace; text-align: center; margin: 20px 0; font-size: 18px; letter-spacing: 2px; }}
                .button {{ display: inline-block; padding: 14px 32px; background: #d97757; color: #fff; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #888; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
                    <h2 style="color: #d97757;">Willkommen bei 0711!</h2>
                    <p>Hallo {name},</p>
                    <p>Ihr Konto wurde erfolgreich eingerichtet. Hier ist Ihr Lizenzschlüssel:</p>
                    <div class="license">{license_key}</div>
                    <p>Sie können jetzt 0711 herunterladen und installieren:</p>
                    <p style="text-align: center;">
                        <a href="{settings.website_url}/download" class="button">0711 herunterladen</a>
                    </p>
                    <h3 style="color: #faf9f5;">Nächste Schritte:</h3>
                    <ol style="color: #ccc;">
                        <li>Installer herunterladen</li>
                        <li>0711 installieren</li>
                        <li>Lizenzschlüssel eingeben</li>
                        <li>Mit KI-powered Workflows starten!</li>
                    </ol>
                    <p style="margin-top: 30px;">Bei Fragen stehen wir gerne zur Verfügung: support@0711.io</p>
                </div>
                <div class="footer">
                    <p>© 2024 0711 Intelligence GmbH | Stuttgart, Deutschland</p>
                </div>
            </div>
        </body>
        </html>
        """

        return await cls.send_email(
            to_email=email,
            subject="Willkommen bei 0711 - Ihre Installation ist bereit",
            body_html=html
        )
