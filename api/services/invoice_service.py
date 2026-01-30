"""
Invoice service for generating German-compliant invoices (Rechnungen)
"""

import logging
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
import jinja2
from weasyprint import HTML
from sqlalchemy.orm import Session

from ..models.invoice import Invoice
from ..models.customer import Customer
from ..models.subscription import Subscription
from .email_service import EmailService
from ..config import settings

logger = logging.getLogger(__name__)


class InvoiceService:
    """German invoice generation service"""

    TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

    @classmethod
    async def create_invoice(
        cls,
        db: Session,
        customer: Customer,
        subscription: Subscription,
        billing_email: Optional[str] = None,
        po_number: Optional[str] = None
    ) -> Invoice:
        """
        Create a new invoice for a subscription

        Args:
            db: Database session
            customer: Customer object
            subscription: Subscription object
            billing_email: Email for invoice delivery (defaults to contact_email)
            po_number: Purchase order number

        Returns:
            Created Invoice object
        """
        # Generate invoice number
        invoice_number = await cls._generate_invoice_number(db)

        # Calculate amounts
        if subscription.billing_cycle == "annual":
            net_amount = subscription.price_annual_cents or 0
        else:
            net_amount = subscription.price_monthly_cents or 0

        # VAT calculation
        vat_rate = Decimal("19.00")  # German VAT

        # Reverse charge for EU B2B with valid VAT ID
        if customer.vat_id and customer.country != "DE" and customer.country in cls._eu_countries():
            vat_rate = Decimal("0.00")
            reverse_charge = True
        else:
            reverse_charge = False

        vat_amount = int(Decimal(net_amount) * vat_rate / 100)
        total_amount = net_amount + vat_amount

        # Line items
        period_label = "Jahreslizenz" if subscription.billing_cycle == "annual" else "Monatslizenz"
        line_items = [
            {
                "description": f"0711 {subscription.plan_name} Plan - {period_label}",
                "period": f"{subscription.current_period_start.strftime('%d.%m.%Y')} - {subscription.current_period_end.strftime('%d.%m.%Y')}",
                "quantity": 1,
                "unit_price_cents": net_amount,
                "total_cents": net_amount
            }
        ]

        # Create invoice record
        invoice = Invoice(
            customer_id=customer.id,
            subscription_id=subscription.id,
            invoice_number=invoice_number,
            invoice_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            subtotal_cents=net_amount,
            vat_rate=vat_rate,
            vat_cents=vat_amount,
            total_cents=total_amount,
            currency="EUR",
            line_items=line_items,
            payment_method="invoice",
            payment_status="pending"
        )

        db.add(invoice)
        db.flush()  # Get the ID without committing

        # Generate PDF
        pdf_path = await cls.generate_pdf(invoice, customer, reverse_charge, po_number)
        invoice.pdf_url = pdf_path

        db.commit()
        db.refresh(invoice)

        # Send email
        email_to = billing_email or customer.contact_email
        await EmailService.send_invoice(
            email=email_to,
            invoice=invoice,
            pdf_path=pdf_path
        )

        logger.info(f"Created invoice {invoice_number} for customer {customer.company_name}")
        return invoice

    @classmethod
    async def _generate_invoice_number(cls, db: Session) -> str:
        """Generate unique invoice number: RE-YYYY-NNNN"""
        year = date.today().year

        # Get last invoice number for this year
        last_invoice = (
            db.query(Invoice)
            .filter(Invoice.invoice_number.like(f"RE-{year}-%"))
            .order_by(Invoice.invoice_number.desc())
            .first()
        )

        if last_invoice:
            last_num = int(last_invoice.invoice_number.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"RE-{year}-{new_num:04d}"

    @classmethod
    async def generate_pdf(
        cls,
        invoice: Invoice,
        customer: Customer,
        reverse_charge: bool = False,
        po_number: Optional[str] = None
    ) -> str:
        """
        Generate PDF invoice

        Args:
            invoice: Invoice object
            customer: Customer object
            reverse_charge: Whether reverse charge applies
            po_number: Purchase order number

        Returns:
            Path to generated PDF file
        """
        # Load Jinja2 template
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(cls.TEMPLATE_DIR)
        )
        template = env.get_template("invoice_de.html")

        # Company details
        company = {
            "name": "0711 Intelligence GmbH",
            "street": "Königstraße 1",
            "postal_code": "70173",
            "city": "Stuttgart",
            "country": "Deutschland",
            "vat_id": "DE123456789",
            "register_court": "Amtsgericht Stuttgart",
            "register_number": "HRB 123456",
            "managing_director": "Max Mustermann",
            "bank": "Deutsche Bank",
            "iban": "DE89 3704 0044 0532 0130 00",
            "bic": "COBADEFFXXX"
        }

        # Format amounts for display
        invoice_data = {
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.strftime("%d.%m.%Y"),
            "due_date": invoice.due_date.strftime("%d.%m.%Y"),
            "subtotal": f"{invoice.subtotal_cents / 100:.2f}",
            "vat_rate": float(invoice.vat_rate),
            "vat_amount": f"{invoice.vat_cents / 100:.2f}",
            "total": f"{invoice.total_cents / 100:.2f}",
            "currency": "€"
        }

        # Format line items
        line_items_formatted = []
        for item in invoice.line_items:
            line_items_formatted.append({
                "description": item["description"],
                "period": item.get("period", ""),
                "quantity": item["quantity"],
                "unit_price": f"{item['unit_price_cents'] / 100:.2f}",
                "total": f"{item['total_cents'] / 100:.2f}"
            })

        # Render HTML
        html_content = template.render(
            invoice=invoice_data,
            customer=customer,
            company=company,
            line_items=line_items_formatted,
            reverse_charge=reverse_charge,
            po_number=po_number
        )

        # Generate PDF
        pdf_filename = f"{invoice.invoice_number}.pdf"
        pdf_dir = Path(settings.invoice_storage_path)
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_dir / pdf_filename

        HTML(string=html_content).write_pdf(str(pdf_path))

        logger.info(f"Generated PDF invoice: {pdf_path}")
        return str(pdf_path)

    @classmethod
    def _eu_countries(cls) -> set:
        """Return set of EU country codes"""
        return {
            "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
            "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
            "PL", "PT", "RO", "SK", "SI", "ES", "SE"
        }

    @classmethod
    async def mark_invoice_paid(
        cls,
        db: Session,
        invoice_id: str
    ) -> Invoice:
        """Mark an invoice as paid"""
        from datetime import datetime

        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice not found: {invoice_id}")

        invoice.payment_status = "paid"
        invoice.paid_at = datetime.utcnow()

        db.commit()
        db.refresh(invoice)

        logger.info(f"Marked invoice {invoice.invoice_number} as paid")
        return invoice
