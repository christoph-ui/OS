"""
User Registry

Manages 0711 user accounts in MCP Central user registry
"""
import os
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from passlib.context import CryptContext
from jose import jwt
import uuid

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

USER_REGISTRY_DB = os.getenv(
    "USER_REGISTRY_DB",
    "postgresql://mcp_central:mcp_central_secret@localhost:5434/user_registry"
)

JWT_SECRET = os.getenv("JWT_SECRET", "change_me_in_production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 365


class UserRegistry:
    """Manages user accounts in MCP Central"""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or USER_REGISTRY_DB

    def _get_conn(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)

    async def create_user(
        self,
        customer_id: str,
        email: str,
        full_name: str,
        role: str = "customer_user",
        created_via: str = "api",
        password: Optional[str] = None
    ) -> Dict:
        """
        Create new user account

        Args:
            customer_id: Customer identifier
            email: User email
            full_name: Full name
            role: User role ('customer_admin', 'customer_user')
            created_via: Creation method ('cradle_deployment', 'invitation', 'self_signup')
            password: Optional password (generated if not provided)

        Returns:
            User info with token
        """
        conn = self._get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            # Generate password if not provided
            if not password:
                password = self._generate_password()

            password_hash = pwd_context.hash(password)

            # Insert user
            user_id = str(uuid.uuid4())

            cursor.execute(
                """
                INSERT INTO users (
                    id, customer_id, email, password_hash, full_name, role,
                    status, email_verified, created_via, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    user_id,
                    customer_id,
                    email,
                    password_hash,
                    full_name,
                    role,
                    "active",
                    True,  # Auto-verify for cradle deployments
                    created_via,
                    datetime.now()
                )
            )

            user = cursor.fetchone()
            conn.commit()

            # Generate JWT token
            token = self._generate_token(user)

            logger.info(f"User created: {user_id} ({email})")

            return {
                "id": user_id,
                "customer_id": customer_id,
                "email": email,
                "full_name": full_name,
                "role": role,
                "token": token,
                "password": password if created_via == "cradle_deployment" else None
            }

        finally:
            cursor.close()
            conn.close()

    async def verify_token(self, token: str) -> Dict:
        """
        Verify JWT token and return user info

        Args:
            token: JWT token

        Returns:
            User info from token

        Raises:
            ValueError: If token is invalid
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

            # Check expiration
            if datetime.utcnow() > datetime.fromtimestamp(payload["exp"]):
                raise ValueError("Token expired")

            return {
                "user_id": payload["user_id"],
                "customer_id": payload["customer_id"],
                "email": payload["email"],
                "role": payload["role"]
            }

        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise ValueError(f"Invalid token: {e}")

    async def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        conn = self._get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(
                "SELECT * FROM users WHERE id = %s AND status = 'active'",
                (user_id,)
            )
            user = cursor.fetchone()

            return dict(user) if user else None

        finally:
            cursor.close()
            conn.close()

    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        conn = self._get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(
                "SELECT * FROM users WHERE email = %s AND status = 'active'",
                (email,)
            )
            user = cursor.fetchone()

            return dict(user) if user else None

        finally:
            cursor.close()
            conn.close()

    async def update_user(
        self,
        user_id: str,
        **fields
    ) -> bool:
        """Update user fields"""
        conn = self._get_conn()
        cursor = conn.cursor()

        try:
            # Build SET clause
            set_parts = []
            values = []

            for key, value in fields.items():
                set_parts.append(f"{key} = %s")
                values.append(value)

            if not set_parts:
                return True

            values.append(user_id)

            query = f"UPDATE users SET {', '.join(set_parts)} WHERE id = %s"

            cursor.execute(query, values)
            conn.commit()

            logger.info(f"User updated: {user_id}")
            return True

        finally:
            cursor.close()
            conn.close()

    async def list_users(self, customer_id: str) -> list:
        """List all users for customer"""
        conn = self._get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        try:
            cursor.execute(
                """
                SELECT id, email, full_name, role, status, created_at, last_login_at
                FROM users
                WHERE customer_id = %s AND status != 'deleted'
                ORDER BY created_at DESC
                """,
                (customer_id,)
            )

            users = cursor.fetchall()
            return [dict(user) for user in users]

        finally:
            cursor.close()
            conn.close()

    async def delete_user(self, user_id: str) -> bool:
        """Soft delete user"""
        return await self.update_user(
            user_id,
            status="deleted",
            updated_at=datetime.now()
        )

    def _generate_password(self, length: int = 16) -> str:
        """Generate random password"""
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits + "!@#$%"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def _generate_token(self, user: Dict) -> str:
        """Generate JWT token for user"""
        payload = {
            "sub": str(user["id"]),
            "user_id": str(user["id"]),
            "customer_id": user["customer_id"],
            "email": user["email"],
            "role": user["role"],
            "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS),
            "iat": datetime.utcnow()
        }

        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
