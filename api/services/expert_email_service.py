"""
Expert Email Notification Service
Handles all email communications for the expert network
"""

from typing import Optional, Dict
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from core.config import settings


class ExpertEmailService:
    """Service for sending expert-related emails"""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST if hasattr(settings, 'SMTP_HOST') else "smtp.gmail.com"
        self.smtp_port = settings.SMTP_PORT if hasattr(settings, 'SMTP_PORT') else 587
        self.smtp_user = settings.SMTP_USER if hasattr(settings, 'SMTP_USER') else "noreply@0711.ai"
        self.smtp_password = settings.SMTP_PASSWORD if hasattr(settings, 'SMTP_PASSWORD') else ""
        self.from_email = "0711 Expert Network <experts@0711.ai>"

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject

            # Add text version
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))

            # Add HTML version
            msg.attach(MIMEText(html_content, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            print(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            print(f"Error sending email to {to_email}: {e}")
            return False

    # ========================================================================
    # APPLICATION EMAILS
    # ========================================================================

    def send_application_confirmation(
        self,
        expert_email: str,
        expert_name: str,
        application_id: str
    ) -> bool:
        """Send confirmation email after expert applies"""

        subject = "Application Received - 0711 Expert Network"

        html = f"""
        <html>
        <body style="font-family: 'Lora', Georgia, serif; color: #141413; line-height: 1.7;">
            <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <h1 style="font-family: 'Poppins', Arial, sans-serif; font-size: 28px; font-weight: 600; margin-bottom: 16px;">
                    Welcome to 0711, {expert_name}! 👋
                </h1>

                <p style="font-size: 16px; margin-bottom: 24px;">
                    Thank you for applying to join the 0711 Expert Network. We've received your application and our team is excited to review it.
                </p>

                <div style="background: #faf9f5; padding: 24px; border-radius: 12px; margin-bottom: 24px;">
                    <h3 style="font-family: 'Poppins', Arial, sans-serif; font-size: 16px; margin-bottom: 12px;">
                        What happens next?
                    </h3>
                    <ul style="margin: 0; padding-left: 24px;">
                        <li style="margin-bottom: 8px;">Our team will review your credentials and experience</li>
                        <li style="margin-bottom: 8px;">We'll verify your certifications and documents</li>
                        <li style="margin-bottom: 8px;">You'll hear back from us within <strong>2-5 business days</strong></li>
                    </ul>
                </div>

                <p style="font-size: 14px; color: #b0aea5; margin-bottom: 16px;">
                    <strong>Application ID:</strong> {application_id}
                </p>

                <p style="font-size: 14px;">
                    Questions? Reply to this email or contact us at <a href="mailto:experts@0711.ai" style="color: #d97757;">experts@0711.ai</a>
                </p>

                <hr style="border: none; border-top: 1px solid #e8e6dc; margin: 32px 0;" />

                <p style="font-size: 12px; color: #b0aea5; text-align: center;">
                    0711 Intelligence GmbH · Built for Builders, Not Bureaucrats
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(expert_email, subject, html)

    def send_application_approved(
        self,
        expert_email: str,
        expert_name: str,
        expert_id: str,
        dashboard_url: str = "https://0711.ai/expert/dashboard"
    ) -> bool:
        """Send approval email when expert is accepted"""

        subject = "🎉 You're Approved! Welcome to 0711 Expert Network"

        html = f"""
        <html>
        <body style="font-family: 'Lora', Georgia, serif; color: #141413; line-height: 1.7;">
            <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <div style="text-align: center; margin-bottom: 32px;">
                    <h1 style="font-family: 'Poppins', Arial, sans-serif; font-size: 32px; font-weight: 600; margin-bottom: 16px;">
                        Welcome aboard, {expert_name}! 🚀
                    </h1>
                    <p style="font-size: 18px; color: #b0aea5;">
                        Your application has been approved
                    </p>
                </div>

                <div style="background: #788c5d15; border-left: 4px solid #788c5d; padding: 24px; border-radius: 12px; margin-bottom: 24px;">
                    <p style="font-size: 16px; margin-bottom: 16px;">
                        You're now part of an elite network of AI-powered experts. Here's what happens next:
                    </p>
                    <ul style="margin: 0; padding-left: 24px;">
                        <li style="margin-bottom: 8px;"><strong>Step 1:</strong> Complete your Stripe Connect setup (payout account)</li>
                        <li style="margin-bottom: 8px;"><strong>Step 2:</strong> Take the MCP certification course (optional but recommended)</li>
                        <li style="margin-bottom: 8px;"><strong>Step 3:</strong> Get matched with your first client (usually within 24-48 hours)</li>
                    </ul>
                </div>

                <div style="text-align: center; margin: 32px 0;">
                    <a href="{dashboard_url}" style="
                        display: inline-block;
                        padding: 16px 32px;
                        background: #d97757;
                        color: white;
                        text-decoration: none;
                        border-radius: 100px;
                        font-family: 'Poppins', Arial, sans-serif;
                        font-weight: 600;
                        font-size: 16px;
                    ">
                        Access Your Dashboard
                    </a>
                </div>

                <div style="background: #faf9f5; padding: 24px; border-radius: 12px; margin-bottom: 24px;">
                    <h3 style="font-family: 'Poppins', Arial, sans-serif; font-size: 16px; margin-bottom: 12px;">
                        💰 Your Earnings Potential
                    </h3>
                    <p style="font-size: 14px;">
                        As a 0711 expert with your expertise, you can expect to earn <strong>€25,000-€35,000/month</strong> serving 7-10 clients. You keep 90%, we take 10%.
                    </p>
                </div>

                <p style="font-size: 14px;">
                    Questions? Our expert success team is here to help: <a href="mailto:experts@0711.ai" style="color: #d97757;">experts@0711.ai</a>
                </p>

                <hr style="border: none; border-top: 1px solid #e8e6dc; margin: 32px 0;" />

                <p style="font-size: 12px; color: #b0aea5; text-align: center;">
                    0711 Intelligence GmbH · Built for Builders, Not Bureaucrats
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(expert_email, subject, html)

    def send_application_rejected(
        self,
        expert_email: str,
        expert_name: str,
        rejection_reason: str
    ) -> bool:
        """Send rejection email with feedback"""

        subject = "Update on Your 0711 Expert Application"

        html = f"""
        <html>
        <body style="font-family: 'Lora', Georgia, serif; color: #141413; line-height: 1.7;">
            <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <h1 style="font-family: 'Poppins', Arial, sans-serif; font-size: 24px; font-weight: 600; margin-bottom: 16px;">
                    Thank you for your interest, {expert_name}
                </h1>

                <p style="font-size: 16px; margin-bottom: 24px;">
                    After careful review, we've decided not to move forward with your application at this time.
                </p>

                <div style="background: #faf9f5; padding: 24px; border-radius: 12px; margin-bottom: 24px;">
                    <h3 style="font-family: 'Poppins', Arial, sans-serif; font-size: 14px; margin-bottom: 12px; color: #b0aea5;">
                        FEEDBACK
                    </h3>
                    <p style="font-size: 14px;">
                        {rejection_reason}
                    </p>
                </div>

                <p style="font-size: 14px; margin-bottom: 16px;">
                    We encourage you to reapply in the future once you've addressed the feedback above. The 0711 network is always looking for exceptional talent.
                </p>

                <p style="font-size: 14px;">
                    Questions? Contact us at <a href="mailto:experts@0711.ai" style="color: #d97757;">experts@0711.ai</a>
                </p>

                <hr style="border: none; border-top: 1px solid #e8e6dc; margin: 32px 0;" />

                <p style="font-size: 12px; color: #b0aea5; text-align: center;">
                    0711 Intelligence GmbH
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(expert_email, subject, html)

    # ========================================================================
    # ENGAGEMENT EMAILS
    # ========================================================================

    def send_new_client_matched(
        self,
        expert_email: str,
        expert_name: str,
        company_name: str,
        mcps: list,
        monthly_rate: int,
        intro_call_url: str
    ) -> bool:
        """Notify expert of new client match"""

        subject = f"🎯 New Client Matched: {company_name}"

        html = f"""
        <html>
        <body style="font-family: 'Lora', Georgia, serif; color: #141413; line-height: 1.7;">
            <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <h1 style="font-family: 'Poppins', Arial, sans-serif; font-size: 28px; font-weight: 600; margin-bottom: 16px;">
                    Great news, {expert_name}! 🎉
                </h1>

                <p style="font-size: 16px; margin-bottom: 24px;">
                    We've matched you with a new client: <strong>{company_name}</strong>
                </p>

                <div style="background: #faf9f5; padding: 24px; border-radius: 12px; margin-bottom: 24px;">
                    <h3 style="font-family: 'Poppins', Arial, sans-serif; font-size: 16px; margin-bottom: 16px;">
                        Engagement Details
                    </h3>
                    <p style="margin-bottom: 8px;"><strong>Company:</strong> {company_name}</p>
                    <p style="margin-bottom: 8px;"><strong>MCPs Needed:</strong> {', '.join(mcps)}</p>
                    <p style="margin-bottom: 8px;"><strong>Monthly Rate:</strong> €{monthly_rate:,}</p>
                    <p style="margin-bottom: 8px;"><strong>Your Earnings (90%):</strong> €{int(monthly_rate * 0.9):,}</p>
                </div>

                <div style="text-align: center; margin: 32px 0;">
                    <a href="{intro_call_url}" style="
                        display: inline-block;
                        padding: 16px 32px;
                        background: #d97757;
                        color: white;
                        text-decoration: none;
                        border-radius: 100px;
                        font-family: 'Poppins', Arial, sans-serif;
                        font-weight: 600;
                        font-size: 16px;
                    ">
                        Schedule Intro Call
                    </a>
                </div>

                <p style="font-size: 14px; color: #b0aea5;">
                    The client is expecting to hear from you within <strong>2 hours</strong> to maintain your response time rating.
                </p>

                <hr style="border: none; border-top: 1px solid #e8e6dc; margin: 32px 0;" />

                <p style="font-size: 12px; color: #b0aea5; text-align: center;">
                    0711 Intelligence GmbH
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(expert_email, subject, html)

    def send_company_expert_confirmed(
        self,
        company_email: str,
        company_name: str,
        expert_name: str,
        expert_headline: str,
        mcps: list,
        monthly_rate: int,
        dashboard_url: str
    ) -> bool:
        """Notify company that expert engagement is confirmed"""

        subject = f"✓ Expert Confirmed: {expert_name}"

        html = f"""
        <html>
        <body style="font-family: 'Lora', Georgia, serif; color: #141413; line-height: 1.7;">
            <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <h1 style="font-family: 'Poppins', Arial, sans-serif; font-size: 28px; font-weight: 600; margin-bottom: 16px;">
                    Your Expert is Ready! 🚀
                </h1>

                <p style="font-size: 16px; margin-bottom: 24px;">
                    {expert_name} has accepted your engagement and is ready to start working with {company_name}.
                </p>

                <div style="background: #faf9f5; padding: 24px; border-radius: 12px; margin-bottom: 24px;">
                    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
                        <div style="
                            width: 64px;
                            height: 64px;
                            border-radius: 16px;
                            background: linear-gradient(135deg, #d97757, #6a9bcc);
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            color: white;
                            font-family: 'Poppins', Arial, sans-serif;
                            font-size: 24px;
                            font-weight: 600;
                        ">
                            {expert_name[0]}{expert_name.split()[-1][0]}
                        </div>
                        <div>
                            <h3 style="font-family: 'Poppins', Arial, sans-serif; font-size: 18px; font-weight: 600; margin: 0 0 4px 0;">
                                {expert_name}
                            </h3>
                            <p style="font-size: 14px; color: #b0aea5; margin: 0;">
                                {expert_headline}
                            </p>
                        </div>
                    </div>
                    <p style="margin-bottom: 8px;"><strong>MCPs:</strong> {', '.join(mcps)}</p>
                    <p style="margin-bottom: 8px;"><strong>Monthly Rate:</strong> €{monthly_rate:,}</p>
                    <p style="margin-bottom: 0;"><strong>Next Steps:</strong> Your expert will reach out within 2 hours to schedule an intro call.</p>
                </div>

                <div style="text-align: center; margin: 32px 0;">
                    <a href="{dashboard_url}" style="
                        display: inline-block;
                        padding: 16px 32px;
                        background: #141413;
                        color: white;
                        text-decoration: none;
                        border-radius: 100px;
                        font-family: 'Poppins', Arial, sans-serif;
                        font-weight: 600;
                        font-size: 16px;
                    ">
                        View in Dashboard
                    </a>
                </div>

                <hr style="border: none; border-top: 1px solid #e8e6dc; margin: 32px 0;" />

                <p style="font-size: 12px; color: #b0aea5; text-align: center;">
                    0711 Intelligence GmbH
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(company_email, subject, html)

    # ========================================================================
    # QUALITY & PERFORMANCE EMAILS
    # ========================================================================

    def send_tier_promotion(
        self,
        expert_email: str,
        expert_name: str,
        new_tier: str,
        old_tier: str,
        quality_score: float
    ) -> bool:
        """Notify expert of tier promotion (e.g., Silver → Gold)"""

        tier_emojis = {
            'platinum': '💎',
            'gold': '🥇',
            'silver': '🥈',
            'standard': '✓',
        }

        subject = f"{tier_emojis.get(new_tier, '🎉')} You've been promoted to {new_tier.capitalize()} tier!"

        html = f"""
        <html>
        <body style="font-family: 'Lora', Georgia, serif; color: #141413; line-height: 1.7;">
            <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <h1 style="font-family: 'Poppins', Arial, sans-serif; font-size: 28px; font-weight: 600; margin-bottom: 16px;">
                    Congratulations, {expert_name}! {tier_emojis.get(new_tier, '🎉')}
                </h1>

                <p style="font-size: 16px; margin-bottom: 24px;">
                    Your exceptional performance has earned you a promotion from <strong>{old_tier.capitalize()}</strong> to <strong>{new_tier.capitalize()}</strong> tier.
                </p>

                <div style="background: #788c5d15; padding: 24px; border-radius: 12px; margin-bottom: 24px;">
                    <p style="margin-bottom: 12px;"><strong>Your Quality Score:</strong> {quality_score:.1f}/100</p>
                    <p style="margin-bottom: 12px;"><strong>New Tier:</strong> {new_tier.capitalize()} (Top {'10%' if new_tier == 'platinum' else '25%' if new_tier == 'gold' else '50%'})</p>
                    <p style="margin-bottom: 0;"><strong>Benefits:</strong></p>
                    <ul style="margin-top: 8px; padding-left: 24px;">
                        {'<li>Featured placement in marketplace</li>' if new_tier == 'platinum' else ''}
                        {'<li>+5% revenue bonus</li>' if new_tier == 'platinum' else '<li>+2% revenue bonus</li>' if new_tier == 'gold' else ''}
                        <li>Higher visibility to potential clients</li>
                    </ul>
                </div>

                <p style="font-size: 14px;">
                    Keep up the great work! Your clients love working with you.
                </p>

                <hr style="border: none; border-top: 1px solid #e8e6dc; margin: 32px 0;" />

                <p style="font-size: 12px; color: #b0aea5; text-align: center;">
                    0711 Intelligence GmbH
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(expert_email, subject, html)

    def send_probation_warning(
        self,
        expert_email: str,
        expert_name: str,
        quality_score: float,
        improvement_areas: list
    ) -> bool:
        """Notify expert they're on probation"""

        subject = "⚠️ Important: Quality Improvement Plan Required"

        html = f"""
        <html>
        <body style="font-family: 'Lora', Georgia, serif; color: #141413; line-height: 1.7;">
            <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <h1 style="font-family: 'Poppins', Arial, sans-serif; font-size: 24px; font-weight: 600; margin-bottom: 16px;">
                    Quality Improvement Plan - Action Required
                </h1>

                <p style="font-size: 16px; margin-bottom: 24px;">
                    Hi {expert_name},
                </p>

                <p style="font-size: 16px; margin-bottom: 24px;">
                    We've noticed your quality score has dropped below our standards. Your current score is <strong>{quality_score:.1f}/100</strong> (minimum required: 60).
                </p>

                <div style="background: #c75a5a15; border-left: 4px solid #c75a5a; padding: 24px; border-radius: 12px; margin-bottom: 24px;">
                    <h3 style="font-family: 'Poppins', Arial, sans-serif; font-size: 16px; margin-bottom: 12px;">
                        Areas for Improvement:
                    </h3>
                    <ul style="margin: 0; padding-left: 24px;">
                        {''.join(f'<li style="margin-bottom: 8px;">{area}</li>' for area in improvement_areas)}
                    </ul>
                </div>

                <div style="background: #faf9f5; padding: 24px; border-radius: 12px; margin-bottom: 24px;">
                    <h3 style="font-family: 'Poppins', Arial, sans-serif; font-size: 16px; margin-bottom: 12px;">
                        What happens next:
                    </h3>
                    <ul style="margin: 0; padding-left: 24px;">
                        <li style="margin-bottom: 8px;">You have <strong>30 days</strong> to improve your quality score</li>
                        <li style="margin-bottom: 8px;">No new clients will be assigned during this period</li>
                        <li style="margin-bottom: 8px;">Weekly check-ins with our success team</li>
                        <li style="margin-bottom: 8px;">Training resources and support provided</li>
                    </ul>
                </div>

                <p style="font-size: 14px;">
                    We believe in you and want to see you succeed. Our team is here to support your improvement journey.
                </p>

                <p style="font-size: 14px;">
                    Questions or need support? Contact: <a href="mailto:experts@0711.ai" style="color: #d97757;">experts@0711.ai</a>
                </p>

                <hr style="border: none; border-top: 1px solid #e8e6dc; margin: 32px 0;" />

                <p style="font-size: 12px; color: #b0aea5; text-align: center;">
                    0711 Intelligence GmbH
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(expert_email, subject, html)

    # ========================================================================
    # WEEKLY DIGEST
    # ========================================================================

    def send_weekly_summary(
        self,
        expert_email: str,
        expert_name: str,
        weekly_stats: Dict
    ) -> bool:
        """Send weekly performance summary to expert"""

        subject = f"📊 Your Week at 0711: {weekly_stats['tasks_completed']} tasks, €{weekly_stats['payout']:,} payout"

        html = f"""
        <html>
        <body style="font-family: 'Lora', Georgia, serif; color: #141413; line-height: 1.7;">
            <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <h1 style="font-family: 'Poppins', Arial, sans-serif; font-size: 24px; font-weight: 600; margin-bottom: 8px;">
                    Week in Review
                </h1>
                <p style="color: #b0aea5; margin-bottom: 32px;">
                    {datetime.utcnow().strftime('%B %d, %Y')}
                </p>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 32px;">
                    <div style="background: #faf9f5; padding: 20px; border-radius: 12px; text-align: center;">
                        <p style="font-size: 12px; color: #b0aea5; margin-bottom: 4px;">Tasks Completed</p>
                        <p style="font-family: 'Poppins', Arial, sans-serif; font-size: 32px; font-weight: 600; color: #788c5d; margin: 0;">
                            {weekly_stats['tasks_completed']}
                        </p>
                    </div>
                    <div style="background: #faf9f5; padding: 20px; border-radius: 12px; text-align: center;">
                        <p style="font-size: 12px; color: #b0aea5; margin-bottom: 4px;">Weekly Payout</p>
                        <p style="font-family: 'Poppins', Arial, sans-serif; font-size: 32px; font-weight: 600; color: #788c5d; margin: 0;">
                            €{weekly_stats['payout']:,}
                        </p>
                    </div>
                </div>

                <div style="background: #faf9f5; padding: 24px; border-radius: 12px; margin-bottom: 24px;">
                    <p style="margin-bottom: 8px;"><strong>AI Automation:</strong> {weekly_stats['ai_automation']}%</p>
                    <p style="margin-bottom: 8px;"><strong>Avg Response Time:</strong> {weekly_stats['avg_response_time']}</p>
                    <p style="margin-bottom: 8px;"><strong>Client Satisfaction:</strong> {weekly_stats['client_satisfaction']}/5 ⭐</p>
                    <p style="margin-bottom: 0;"><strong>Active Clients:</strong> {weekly_stats['active_clients']}</p>
                </div>

                <p style="font-size: 14px; text-align: center; color: #b0aea5;">
                    Your next payout will be deposited on Friday
                </p>

                <hr style="border: none; border-top: 1px solid #e8e6dc; margin: 32px 0;" />

                <p style="font-size: 12px; color: #b0aea5; text-align: center;">
                    0711 Intelligence GmbH
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(expert_email, subject, html)


# Singleton instance
expert_email_service = ExpertEmailService()
