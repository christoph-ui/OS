"""
Partner Management Routes
Handles partner registration, customer creation, and management
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import uuid
import secrets

from ..database import get_db
from ..models.partner import Partner
from ..models.customer import Customer
from ..models.user import User, UserRole, UserStatus
from ..schemas.partner import (
    PartnerCreate,
    PartnerResponse,
    PartnerDetailResponse,
    PartnerUpdate,
    PartnerLoginRequest,
    PartnerLoginResponse,
    PartnerCustomerCreate,
    PartnerCustomerResponse,
    PartnerCustomerListResponse,
    PartnerDashboardResponse
)
from ..utils.security import (
    get_current_user,
    get_current_partner,
    hash_password,
    verify_password,
    create_access_token
)

router = APIRouter(prefix="/api/partners", tags=["partners"])


@router.post("/register", response_model=PartnerResponse, status_code=status.HTTP_201_CREATED)
async def register_partner(
    partner_data: PartnerCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new partner (agency/reseller)

    Creates a partner account + primary admin user
    """
    # Check if email already exists
    existing_partner = db.query(Partner).filter(
        Partner.contact_email == partner_data.contact_email
    ).first()

    if existing_partner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-Mail already registered"
        )

    # Check if user exists
    existing_user = db.query(User).filter(User.email == partner_data.contact_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-Mail already registered"
        )

    # Create partner
    partner = Partner(
        company_name=partner_data.company_name,
        contact_email=partner_data.contact_email,
        contact_phone=partner_data.contact_phone,
        street=partner_data.street,
        city=partner_data.city,
        postal_code=partner_data.postal_code,
        country=partner_data.country,
        vat_id=partner_data.vat_id,
        status="active",
        email_verified=True  # Auto-verify for now
    )

    db.add(partner)
    db.flush()  # Get partner.id

    # Split contact_name into first_name and last_name
    name_parts = partner_data.contact_name.strip().split(' ', 1) if partner_data.contact_name else ['', '']
    first_name = name_parts[0] or 'Admin'
    last_name = name_parts[1] if len(name_parts) > 1 else ''

    # Create partner admin user
    admin_user = User(
        id=uuid.uuid4(),
        partner_id=partner.id,
        customer_id=None,  # Partner admins don't belong to customers
        email=partner_data.contact_email,
        password_hash=hash_password(partner_data.password),
        first_name=first_name,
        last_name=last_name,
        role=UserRole.PARTNER_ADMIN,  # Now safe with values_callable fix
        status=UserStatus.ACTIVE,     # Now safe with values_callable fix
        permissions={
            "customers.create": True,
            "customers.manage_multiple": True,
            "customers.view_all_own": True,
            "users.manage_all_customers": True
        },
        email_verified=True
    )

    db.add(admin_user)
    db.commit()
    db.refresh(partner)

    return PartnerResponse.from_orm(partner)


@router.post("/login", response_model=PartnerLoginResponse)
async def partner_login(
    request: PartnerLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Partner login

    Validates credentials and returns JWT token
    """
    # Get partner admin user by email
    user = db.query(User).filter(
        User.email == request.email,
        User.role == UserRole.PARTNER_ADMIN
    ).first()

    # Verify password
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated"
        )

    # Get partner
    partner = db.query(Partner).filter(Partner.id == user.partner_id).first()

    if not partner or not partner.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Partner account is not active"
        )

    # Update login tracking
    user.last_login_at = datetime.utcnow()
    user.login_count += 1
    db.commit()

    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "user_id": str(user.id),
            "email": user.email,
            "partner_id": str(partner.id),
            "role": user.role.value
        }
    )

    return PartnerLoginResponse(
        access_token=access_token,
        token_type="bearer",
        partner=PartnerResponse.from_orm(partner),
        user_id=user.id
    )


@router.get("/me", response_model=PartnerDetailResponse)
async def get_partner_profile(
    partner: Partner = Depends(get_current_partner)
):
    """
    Get current partner profile
    """
    return PartnerDetailResponse.from_orm(partner)


@router.patch("/me", response_model=PartnerDetailResponse)
async def update_partner_profile(
    updates: PartnerUpdate,
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """
    Update partner profile
    """
    # Apply updates
    if updates.company_name is not None:
        partner.company_name = updates.company_name

    if updates.contact_email is not None:
        # Check if email already exists
        existing = db.query(Partner).filter(
            Partner.contact_email == updates.contact_email,
            Partner.id != partner.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        partner.contact_email = updates.contact_email

    if updates.contact_phone is not None:
        partner.contact_phone = updates.contact_phone

    if updates.street is not None:
        partner.street = updates.street

    if updates.city is not None:
        partner.city = updates.city

    if updates.postal_code is not None:
        partner.postal_code = updates.postal_code

    if updates.country is not None:
        partner.country = updates.country

    if updates.vat_id is not None:
        partner.vat_id = updates.vat_id

    partner.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(partner)

    return PartnerDetailResponse.from_orm(partner)


@router.post("/customers", response_model=PartnerCustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: PartnerCustomerCreate,
    partner: Partner = Depends(get_current_partner),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Partner creates a new customer account

    This customer will be managed by the partner.
    """
    # Check if email already exists
    existing_customer = db.query(Customer).filter(
        Customer.contact_email == customer_data.contact_email
    ).first()

    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email already exists"
        )

    existing_user = db.query(User).filter(User.email == customer_data.contact_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Generate random password (will be sent via invitation)
    temp_password = secrets.token_urlsafe(16)

    # Create customer
    customer = Customer(
        company_name=customer_data.company_name,
        company_type=customer_data.company_type,
        vat_id=customer_data.vat_id,
        street=customer_data.street,
        city=customer_data.city,
        postal_code=customer_data.postal_code,
        country=customer_data.country,
        contact_name=customer_data.contact_name,
        contact_email=customer_data.contact_email,
        contact_phone=customer_data.contact_phone,
        password_hash=hash_password(temp_password),  # Legacy field
        tier=customer_data.tier,
        source="partner",
        status="active",
        partner_id=partner.id,  # Link to partner
        onboarding_status="not_started"
    )

    db.add(customer)
    db.flush()  # Get customer.id

    # Split contact_name into first_name and last_name
    name_parts = customer_data.contact_name.strip().split(' ', 1) if customer_data.contact_name else ['', '']
    first_name = name_parts[0] or 'Admin'
    last_name = name_parts[1] if len(name_parts) > 1 else ''

    # Create customer admin user
    if customer_data.send_invitation:
        # Create user in invited state
        customer_admin = User(
            id=uuid.uuid4(),
            customer_id=customer.id,
            email=customer_data.contact_email,
            first_name=first_name,
            last_name=last_name,
            role="customer_admin",  # Direct string (lowercase)
            status="invited",       # Direct string (lowercase)
            permissions={
                "billing.view": True,
                "billing.edit": True,
                "users.invite": True,
                "users.manage": True,
                "mcps.install": True,
                "data.view": True,
                "data.edit": True
            },
            invited_by_id=user.id,
            invited_at=datetime.utcnow(),
            email_verified=False
        )
    else:
        # Create active user with temp password
        customer_admin = User(
            id=uuid.uuid4(),
            customer_id=customer.id,
            email=customer_data.contact_email,
            password_hash=hash_password(temp_password),
            first_name=first_name,
            last_name=last_name,
            role="customer_admin",  # Direct string (lowercase)
            status="active",        # Direct string (lowercase)
            permissions={
                "billing.view": True,
                "billing.edit": True,
                "users.invite": True,
                "users.manage": True,
                "mcps.install": True,
                "data.view": True,
                "data.edit": True
            },
            email_verified=True
        )

    db.add(customer_admin)
    db.flush()

    # Set as primary admin
    customer.primary_admin_id = customer_admin.id

    db.commit()
    db.refresh(customer)

    # TODO: Send invitation email if send_invitation=True

    return PartnerCustomerResponse.from_orm(customer)


@router.get("/customers", response_model=PartnerCustomerListResponse)
async def list_partner_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """
    List all customers managed by this partner

    Filtered to only show customers belonging to the current partner.
    """
    # Query customers for this partner
    query = db.query(Customer).filter(Customer.partner_id == partner.id)

    if status:
        query = query.filter(Customer.status == status)

    # Get total count
    total = query.count()

    # Paginate
    customers = query.order_by(Customer.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return PartnerCustomerListResponse(
        customers=[PartnerCustomerResponse.from_orm(c) for c in customers],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/customers/{customer_id}", response_model=PartnerCustomerResponse)
async def get_partner_customer(
    customer_id: UUID,
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """
    Get customer details

    Only customers belonging to this partner can be accessed.
    """
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.partner_id == partner.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found or does not belong to this partner"
        )

    return PartnerCustomerResponse.from_orm(customer)


@router.get("/dashboard", response_model=PartnerDashboardResponse)
async def get_partner_dashboard(
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """
    Get partner dashboard with statistics

    Shows total customers, active customers, revenue, etc.
    """
    # Get all customers for this partner
    customers = db.query(Customer).filter(Customer.partner_id == partner.id).all()

    total_customers = len(customers)
    active_customers = len([c for c in customers if c.status == "active"])
    customers_onboarding = len([c for c in customers if c.onboarding_status != "completed"])

    # TODO: Calculate total revenue from subscriptions
    total_revenue = 0.0

    # Get recent customers (last 5)
    recent_customers = db.query(Customer).filter(
        Customer.partner_id == partner.id
    ).order_by(Customer.created_at.desc()).limit(5).all()

    return PartnerDashboardResponse(
        partner_id=partner.id,
        company_name=partner.company_name,
        total_customers=total_customers,
        active_customers=active_customers,
        total_revenue=total_revenue,
        customers_onboarding=customers_onboarding,
        recent_customers=[PartnerCustomerResponse.from_orm(c) for c in recent_customers]
    )


@router.patch("/customers/{customer_id}", response_model=PartnerCustomerResponse)
async def update_customer(
    customer_id: UUID,
    updates: "CustomerUpdate",
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """
    Update customer information

    Only customers belonging to this partner can be updated.
    """
    from ..schemas.customer import CustomerUpdate

    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.partner_id == partner.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found or does not belong to this partner"
        )

    # Apply updates
    if updates.company_name is not None:
        customer.company_name = updates.company_name

    if updates.company_type is not None:
        customer.company_type = updates.company_type

    if updates.vat_id is not None:
        customer.vat_id = updates.vat_id

    if updates.contact_name is not None:
        customer.contact_name = updates.contact_name

    if updates.contact_email is not None:
        # Check if email already exists
        existing = db.query(Customer).filter(
            Customer.contact_email == updates.contact_email,
            Customer.id != customer_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        customer.contact_email = updates.contact_email

    if updates.contact_phone is not None:
        customer.contact_phone = updates.contact_phone

    if updates.street is not None:
        customer.street = updates.street

    if updates.city is not None:
        customer.city = updates.city

    if updates.postal_code is not None:
        customer.postal_code = updates.postal_code

    customer.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(customer)

    return PartnerCustomerResponse.from_orm(customer)


@router.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: UUID,
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """
    Delete a customer

    Only customers belonging to this partner can be deleted.
    WARNING: This will cascade delete all related data (deployments, users, etc.)
    """
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.partner_id == partner.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found or does not belong to this partner"
        )

    # Store company name for response
    company_name = customer.company_name

    # Delete customer (CASCADE will handle related records)
    db.delete(customer)
    db.commit()

    return {
        "success": True,
        "message": f"Customer '{company_name}' deleted successfully",
        "customer_id": str(customer_id)
    }


@router.post("/customers/bulk-delete")
async def bulk_delete_customers(
    customer_ids: List[UUID],
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """
    Delete multiple customers at once

    Only customers belonging to this partner can be deleted.
    WARNING: This will cascade delete all related data for each customer.
    """
    # Verify all customers belong to this partner
    customers = db.query(Customer).filter(
        Customer.id.in_(customer_ids),
        Customer.partner_id == partner.id
    ).all()

    if len(customers) != len(customer_ids):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Some customers do not belong to this partner or do not exist"
        )

    # Delete all customers
    deleted_count = 0
    deleted_names = []

    for customer in customers:
        deleted_names.append(customer.company_name)
        db.delete(customer)
        deleted_count += 1

    db.commit()

    return {
        "success": True,
        "message": f"Successfully deleted {deleted_count} customers",
        "deleted_count": deleted_count,
        "deleted_customers": deleted_names
    }


@router.post("/customers/{customer_id}/impersonate")
async def impersonate_customer(
    customer_id: UUID,
    partner: Partner = Depends(get_current_partner),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate temporary token to impersonate customer (for support/demo)

    Security:
    - Only works if customer belongs to THIS partner
    - Token expires in 1 hour
    - All actions logged to audit log
    - Console shows impersonation banner
    """
    # CRITICAL: Verify customer belongs to partner
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.partner_id == partner.id  # Security check!
    ).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer not found or you don't have permission"
        )

    # Get customer admin user
    customer_admin = db.query(User).filter(
        User.id == customer.primary_admin_id
    ).first()

    if not customer_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer admin user not found"
        )

    # Create impersonation token (1 hour expiry)
    from datetime import timedelta
    import time

    impersonate_token = create_access_token(
        data={
            "sub": str(customer_admin.id),
            "user_id": str(customer_admin.id),
            "email": customer_admin.email,
            "customer_id": str(customer.id),
            "role": "customer_admin",
            "impersonated_by": str(partner.id),  # Track who impersonates
            "impersonated_by_email": user.email,
            "impersonate_expires": int(time.time()) + 3600  # 1 hour
        },
        expires_delta=timedelta(hours=1)
    )

    # Log to audit (if audit_log model exists)
    try:
        from ..models.audit_log import AuditLog

        audit = AuditLog(
            customer_id=customer.id,
            user_id=user.id,
            action="IMPERSONATE",
            resource_type="customer_console",
            resource_id=str(customer.id),
            details={
                "partner_id": str(partner.id),
                "partner_email": user.email,
                "customer_email": customer_admin.email,
                "impersonate_duration": "1 hour"
            }
        )
        db.add(audit)
        db.commit()
    except Exception as e:
        logger.warning(f"Audit logging failed: {e}")

    return {
        "token": impersonate_token,
        "console_url": "http://localhost:4020/",
        "customer_id": str(customer.id),
        "customer_name": customer.company_name,
        "expires_in": 3600,
        "warning": "Sie sehen jetzt Kundendaten. Alle Aktionen werden protokolliert."
    }


@router.get("/customers/{customer_id}/usage")
async def get_customer_usage(
    customer_id: UUID,
    partner: Partner = Depends(get_current_partner),
    db: Session = Depends(get_db)
):
    """
    Get usage statistics for a customer

    Returns queries, documents, storage, and activity data
    """
    # Verify customer belongs to partner
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.partner_id == partner.id
    ).first()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found or does not belong to this partner"
        )

    # Query usage metrics from usage_metrics table
    from ..models.usage import UsageMetric

    metrics = db.query(UsageMetric).filter(
        UsageMetric.customer_id == customer_id
    ).order_by(UsageMetric.created_at.desc()).limit(30).all()

    # Aggregate metrics
    total_queries = sum(m.queries_count or 0 for m in metrics)
    total_tokens = sum(m.tokens_used or 0 for m in metrics)

    # Get latest activity
    last_activity = metrics[0].created_at if metrics else None

    # Get document count from lakehouse (if available)
    documents_ingested = 0
    storage_used_mb = 0

    # TODO: Query lakehouse for actual document count and storage
    # For now, return placeholder data

    return {
        "customer_id": str(customer_id),
        "total_queries": total_queries,
        "total_tokens": total_tokens,
        "documents_ingested": documents_ingested,
        "storage_used_mb": storage_used_mb,
        "last_activity": last_activity.isoformat() if last_activity else None,
        "metrics_count": len(metrics)
    }
