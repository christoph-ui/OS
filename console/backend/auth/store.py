"""
User Store

In-memory user storage (replace with database in production).
"""

from typing import Dict, Optional
import logging

from .models import User, UserInDB, UserCreate
from .jwt import get_password_hash

logger = logging.getLogger(__name__)

# In-memory user store (replace with database)
# Structure: {user_id: UserInDB}
_users: Dict[str, UserInDB] = {}

# Email to user_id mapping for quick lookup
_email_to_id: Dict[str, str] = {}


async def create_user(user_create: UserCreate) -> User:
    """
    Create a new user.

    Args:
        user_create: User creation data

    Returns:
        Created user (without password)

    Raises:
        ValueError if email already exists
    """
    # Check if email exists
    if user_create.email.lower() in _email_to_id:
        raise ValueError("Email already registered")

    # Create user
    user = UserInDB(
        email=user_create.email.lower(),
        name=user_create.name,
        customer_id=user_create.customer_id,
        hashed_password=get_password_hash(user_create.password)
    )

    # Store
    _users[user.id] = user
    _email_to_id[user.email] = user.id

    logger.info(f"Created user: {user.email} (customer: {user.customer_id})")

    # Return without password
    return User(**user.model_dump(exclude={"hashed_password"}))


async def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Get user by email"""
    email = email.lower()
    user_id = _email_to_id.get(email)
    if user_id:
        return _users.get(user_id)
    return None


async def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID (without password)"""
    from ..config import config

    # Test mode: Return mock user
    if config.testing and user_id.startswith("test-"):
        return User(
            id=user_id,
            email="test@test.0711.io",
            name="Test User",
            customer_id="test-customer-001",
            is_active=True,
            is_admin=False,
            allowed_mcps=["ctax", "law", "tender"]
        )

    user_in_db = _users.get(user_id)
    if user_in_db:
        return User(**user_in_db.model_dump(exclude={"hashed_password"}))
    return None


async def authenticate_user(email: str, password: str) -> Optional[User]:
    """
    Authenticate user with email and password.

    Returns:
        User if credentials valid, None otherwise
    """
    from .jwt import verify_password

    user = await get_user_by_email(email)
    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    # Update last login
    user.last_login = None  # Would update in real DB

    return User(**user.model_dump(exclude={"hashed_password"}))


async def list_users(customer_id: Optional[str] = None) -> list[User]:
    """List all users, optionally filtered by customer"""
    users = []
    for user_in_db in _users.values():
        if customer_id is None or user_in_db.customer_id == customer_id:
            users.append(User(**user_in_db.model_dump(exclude={"hashed_password"})))
    return users


async def update_user(user_id: str, **updates) -> Optional[User]:
    """Update user fields"""
    if user_id not in _users:
        return None

    user = _users[user_id]
    for key, value in updates.items():
        if hasattr(user, key) and key != "id" and key != "hashed_password":
            setattr(user, key, value)

    return User(**user.model_dump(exclude={"hashed_password"}))


async def delete_user(user_id: str) -> bool:
    """Delete a user"""
    if user_id not in _users:
        return False

    user = _users[user_id]
    del _email_to_id[user.email]
    del _users[user_id]

    logger.info(f"Deleted user: {user.email}")
    return True


# Initialize with a default admin user for development
async def init_default_users():
    """Initialize default users for development with stable UUIDs"""
    try:
        # Create users with deterministic UUIDs (based on email hash)
        import hashlib

        def stable_uuid(email: str) -> str:
            """Generate stable UUID from email"""
            hash_obj = hashlib.md5(email.encode())
            return hash_obj.hexdigest()[:8] + "-" + hash_obj.hexdigest()[8:12] + "-4" + hash_obj.hexdigest()[13:16] + "-" + hash_obj.hexdigest()[16:20] + "-" + hash_obj.hexdigest()[20:32]

        # Enterprise Admin - e-ProCat
        eprocat_user = UserInDB(
            id=stable_uuid("christoph@eprocat.de"),
            email="christoph@eprocat.de",
            name="Christoph Bertsch",
            customer_id="eprocat",
            hashed_password=get_password_hash("0711Enterprise!"),
            is_admin=True
        )
        _users[eprocat_user.id] = eprocat_user
        _email_to_id[eprocat_user.email] = eprocat_user.id

        # Enterprise User - Eaton
        eaton_user = UserInDB(
            id=stable_uuid("michael.weber@eaton.com"),
            email="michael.weber@eaton.com",
            name="Michael Weber",
            customer_id="eaton",
            hashed_password=get_password_hash("Eaton2025"),
            is_admin=True
        )
        _users[eaton_user.id] = eaton_user
        _email_to_id[eaton_user.email] = eaton_user.id

        # Default admin
        admin_user = UserInDB(
            id=stable_uuid("admin@0711.io"),
            email="admin@0711.io",
            name="Admin",
            customer_id="0711",
            hashed_password=get_password_hash("admin123!"),
            is_admin=True
        )
        _users[admin_user.id] = admin_user
        _email_to_id[admin_user.email] = admin_user.id

        # Demo user
        demo_user = UserInDB(
            id=stable_uuid("demo@0711.io"),
            email="demo@0711.io",
            name="Demo User",
            customer_id="demo_corp",
            hashed_password=get_password_hash("demo123")
        )
        _users[demo_user.id] = demo_user
        _email_to_id[demo_user.email] = demo_user.id

        logger.info("Default users initialized with stable UUIDs (4 users)")
    except Exception as e:
        logger.error(f"Error initializing users: {e}")
